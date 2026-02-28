// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import {Test} from "forge-std/Test.sol";
import {CPAMM} from "../src/CPAMM.sol";

contract CPAMMDifferentialTest is Test {
    uint256 internal constant FEE_NUM = 3;
    uint256 internal constant FEE_DEN = 1000;
    CPAMM internal cpamm;

    struct ModelState {
        uint256 x;
        uint256 y;
        uint256 L;
        uint256 lpBalance;
    }

    function setUp() public {
        cpamm = new CPAMM(FEE_NUM, FEE_DEN);
    }

    function _gcd(uint256 a, uint256 b) internal pure returns (uint256) {
        while (b != 0) {
            uint256 t = a % b;
            a = b;
            b = t;
        }
        return a;
    }

    function _assertContractMatches(ModelState memory s) internal view {
        assertEq(cpamm.reserveX(), s.x, "reserveX mismatch");
        assertEq(cpamm.reserveY(), s.y, "reserveY mismatch");
        assertEq(cpamm.totalSupply(), s.L, "totalSupply mismatch");
        assertEq(cpamm.balanceOf(address(this)), s.lpBalance, "LP balance mismatch");
    }

    function _seedPool(uint256 x0, uint256 y0) internal returns (ModelState memory s) {
        uint256 shares0 = cpamm.addLiquidity(x0, y0);
        // Protocol rule at initialization (`totalSupply == 0`): first LP shares equal dx.
        assertEq(shares0, x0, "initial mint mismatch");
        s = ModelState({x: x0, y: y0, L: x0, lpBalance: x0});
        _assertContractMatches(s);
    }

    function _modelSwapXforY(uint256 x, uint256 y, uint256 dx)
        internal
        pure
        returns (uint256 dy, uint256 xNext, uint256 yNext)
    {
        uint256 dxEff = (dx * (FEE_DEN - FEE_NUM)) / FEE_DEN;
        dy = (y * dxEff) / (x + dxEff);
        xNext = x + dx;
        yNext = y - dy;
    }

    function _modelSwapYforX(uint256 x, uint256 y, uint256 dy)
        internal
        pure
        returns (uint256 dx, uint256 xNext, uint256 yNext)
    {
        uint256 dyEff = (dy * (FEE_DEN - FEE_NUM)) / FEE_DEN;
        dx = (x * dyEff) / (y + dyEff);
        xNext = x - dx;
        yNext = y + dy;
    }

    // Exact rational output (no floor on effective input), represented as num/den.
    function _exactDyNoFloor(uint256 x, uint256 y, uint256 dx) internal pure returns (uint256 num, uint256 den) {
        uint256 dxEffNum = dx * (FEE_DEN - FEE_NUM);
        num = y * dxEffNum;
        den = x * FEE_DEN + dxEffNum;
    }

    // Exact rational output (no floor on effective input), represented as num/den.
    function _exactDxNoFloor(uint256 x, uint256 y, uint256 dy) internal pure returns (uint256 num, uint256 den) {
        uint256 dyEffNum = dy * (FEE_DEN - FEE_NUM);
        num = x * dyEffNum;
        den = y * FEE_DEN + dyEffNum;
    }

    function _stepAddProportional(ModelState memory s, uint256 amountSeed) internal returns (ModelState memory) {
        uint256 g = _gcd(s.x, s.y);
        uint256 unitX = s.x / g;
        uint256 unitY = s.y / g;
        uint256 mul = bound(amountSeed, 1, 5);
        uint256 dx = unitX * mul;
        uint256 dy = unitY * mul;

        uint256 shares;
        if (s.L == 0) {
            shares = dx;
        } else {
            shares = (s.L * dx) / s.x;
            uint256 num = s.L * dx;
            uint256 den = s.x;
            assertLe(shares * den, num, "add floor lower-bound violation");
            assertLt(num, (shares + 1) * den, "add floor upper-bound violation");
        }
        assertGt(shares, 0, "zero-share add step");

        uint256 gotShares = cpamm.addLiquidity(dx, dy);
        assertEq(gotShares, shares, "addLiquidity shares mismatch vs model");

        ModelState memory next =
            ModelState({x: s.x + dx, y: s.y + dy, L: s.L + shares, lpBalance: s.lpBalance + shares});
        _assertContractMatches(next);
        return next;
    }

    function _stepRemove(ModelState memory s, uint256 amountSeed) internal returns (ModelState memory) {
        if (s.lpBalance <= 1 || s.L <= 1) {
            return s;
        }

        uint256 maxShares = s.lpBalance;
        if (maxShares >= s.L) {
            maxShares = s.L - 1;
        }
        if (maxShares == 0) {
            return s;
        }
        uint256 shares = bound(amountSeed, 1, maxShares);

        uint256 expectedDx = (s.x * shares) / s.L;
        uint256 expectedDy = (s.y * shares) / s.L;

        uint256 numX = s.x * shares;
        uint256 numY = s.y * shares;
        assertLe(expectedDx * s.L, numX, "remove X floor lower-bound violation");
        assertLt(numX, (expectedDx + 1) * s.L, "remove X floor upper-bound violation");
        assertLe(expectedDy * s.L, numY, "remove Y floor lower-bound violation");
        assertLt(numY, (expectedDy + 1) * s.L, "remove Y floor upper-bound violation");

        (uint256 gotDx, uint256 gotDy) = cpamm.removeLiquidity(shares);
        assertEq(gotDx, expectedDx, "removeLiquidity dx mismatch vs model");
        assertEq(gotDy, expectedDy, "removeLiquidity dy mismatch vs model");

        ModelState memory next = ModelState({
            x: s.x - expectedDx,
            y: s.y - expectedDy,
            L: s.L - shares,
            lpBalance: s.lpBalance - shares
        });
        _assertContractMatches(next);
        return next;
    }

    function _stepSwapX(ModelState memory s, uint256 amountSeed) internal returns (ModelState memory) {
        uint256 maxIn = s.x / 5;
        if (maxIn < 2) {
            return s;
        }
        uint256 dx = bound(amountSeed, 2, maxIn);
        (uint256 expectedDy, uint256 expectedX, uint256 expectedY) = _modelSwapXforY(s.x, s.y, dx);
        if (expectedDy == 0 || expectedDy >= s.y) {
            return s;
        }

        uint256 gotDy = cpamm.swapXforY(dx);
        assertEq(gotDy, expectedDy, "swapXforY dy mismatch vs model");

        ModelState memory next = ModelState({x: expectedX, y: expectedY, L: s.L, lpBalance: s.lpBalance});
        _assertContractMatches(next);
        return next;
    }

    function _stepSwapY(ModelState memory s, uint256 amountSeed) internal returns (ModelState memory) {
        uint256 maxIn = s.y / 5;
        if (maxIn < 2) {
            return s;
        }
        uint256 dy = bound(amountSeed, 2, maxIn);
        (uint256 expectedDx, uint256 expectedX, uint256 expectedY) = _modelSwapYforX(s.x, s.y, dy);
        if (expectedDx == 0 || expectedDx >= s.x) {
            return s;
        }

        uint256 gotDx = cpamm.swapYforX(dy);
        assertEq(gotDx, expectedDx, "swapYforX dx mismatch vs model");

        ModelState memory next = ModelState({x: expectedX, y: expectedY, L: s.L, lpBalance: s.lpBalance});
        _assertContractMatches(next);
        return next;
    }

    function _executeStep(ModelState memory s, uint8 opSeed, uint96 amountSeed) internal returns (ModelState memory) {
        uint256 op = uint256(opSeed) % 4;
        if (op == 0) {
            return _stepAddProportional(s, uint256(amountSeed));
        }
        if (op == 1) {
            return _stepRemove(s, uint256(amountSeed));
        }
        if (op == 2) {
            return _stepSwapX(s, uint256(amountSeed));
        }
        return _stepSwapY(s, uint256(amountSeed));
    }

    function testFuzz_differential_swapXforY_matches_model_and_bound(uint96 sx, uint96 sy, uint96 sdx) public {
        uint256 x0 = bound(uint256(sx), 1_000_000, 10**20);
        uint256 y0 = bound(uint256(sy), 1_000_000, 10**20);
        cpamm.addLiquidity(x0, y0);

        uint256 dx = bound(uint256(sdx), (x0 / 1_000_000) + 2, x0 / 5);

        (uint256 expectedDy, uint256 expectedX, uint256 expectedY) = _modelSwapXforY(x0, y0, dx);
        vm.assume(expectedDy > 0);
        uint256 gotDy = cpamm.swapXforY(dx);

        assertEq(gotDy, expectedDy, "swapXforY dy mismatch vs reference model");
        assertEq(cpamm.reserveX(), expectedX, "swapXforY reserveX mismatch vs reference model");
        assertEq(cpamm.reserveY(), expectedY, "swapXforY reserveY mismatch vs reference model");
        assertGt(cpamm.reserveY(), 0, "swapXforY reserveY must remain positive");

        // Lean-style bound: floor-rounded output is bounded by exact rational output.
        (uint256 num, uint256 den) = _exactDyNoFloor(x0, y0, dx);
        assertLe(gotDy * den, num, "swapXforY floor output exceeds exact rational output");
    }

    function testFuzz_differential_swapYforX_matches_model_and_bound(uint96 sx, uint96 sy, uint96 sdy) public {
        uint256 x0 = bound(uint256(sx), 1_000_000, 10**20);
        uint256 y0 = bound(uint256(sy), 1_000_000, 10**20);
        cpamm.addLiquidity(x0, y0);

        uint256 dy = bound(uint256(sdy), (y0 / 1_000_000) + 2, y0 / 5);

        (uint256 expectedDx, uint256 expectedX, uint256 expectedY) = _modelSwapYforX(x0, y0, dy);
        vm.assume(expectedDx > 0);
        uint256 gotDx = cpamm.swapYforX(dy);

        assertEq(gotDx, expectedDx, "swapYforX dx mismatch vs reference model");
        assertEq(cpamm.reserveX(), expectedX, "swapYforX reserveX mismatch vs reference model");
        assertEq(cpamm.reserveY(), expectedY, "swapYforX reserveY mismatch vs reference model");
        assertGt(cpamm.reserveX(), 0, "swapYforX reserveX must remain positive");

        // Lean-style bound: floor-rounded output is bounded by exact rational output.
        (uint256 num, uint256 den) = _exactDxNoFloor(x0, y0, dy);
        assertLe(gotDx * den, num, "swapYforX floor output exceeds exact rational output");
    }

    function testFuzz_differential_three_swap_sequence(uint96 seed, uint96 a, uint96 b, uint96 c) public {
        uint256 x = bound(uint256(seed), 1_000_000, 10**20);
        uint256 y = x;
        cpamm.addLiquidity(x, y);

        uint256 dx1 = bound(uint256(a), (x / 1_000_000) + 2, x / 5);
        (uint256 dy1, uint256 x1, uint256 y1) = _modelSwapXforY(x, y, dx1);
        vm.assume(dy1 > 0);
        assertEq(cpamm.swapXforY(dx1), dy1);
        assertEq(cpamm.reserveX(), x1);
        assertEq(cpamm.reserveY(), y1);

        uint256 dy2In = bound(uint256(b), (y1 / 1_000_000) + 2, y1 / 5);
        (uint256 dx2, uint256 x2, uint256 y2) = _modelSwapYforX(x1, y1, dy2In);
        vm.assume(dx2 > 0);
        assertEq(cpamm.swapYforX(dy2In), dx2);
        assertEq(cpamm.reserveX(), x2);
        assertEq(cpamm.reserveY(), y2);

        uint256 dx3In = bound(uint256(c), (x2 / 1_000_000) + 2, x2 / 5);
        (uint256 dy3, uint256 x3, uint256 y3) = _modelSwapXforY(x2, y2, dx3In);
        vm.assume(dy3 > 0);
        assertEq(cpamm.swapXforY(dx3In), dy3);
        assertEq(cpamm.reserveX(), x3);
        assertEq(cpamm.reserveY(), y3);
        assertGt(cpamm.reserveX(), 0);
        assertGt(cpamm.reserveY(), 0);
    }

    function testFuzz_differential_addLiquidity_matches_model_and_bound(uint64 sx, uint64 sy, uint96 addSeed) public {
        uint256 x0 = bound(uint256(sx), 1_000, 10**9);
        uint256 y0 = bound(uint256(sy), 1_000, 10**9);
        ModelState memory s = _seedPool(x0, y0);

        s = _stepAddProportional(s, uint256(addSeed));

        assertGt(s.x, 0);
        assertGt(s.y, 0);
        assertGt(s.L, 0);
    }

    function testFuzz_differential_removeLiquidity_matches_model_and_bound(
        uint64 sx,
        uint64 sy,
        uint96 removeSeed
    ) public {
        uint256 x0 = bound(uint256(sx), 1_000, 10**9);
        uint256 y0 = bound(uint256(sy), 1_000, 10**9);
        ModelState memory s = _seedPool(x0, y0);

        s = _stepRemove(s, uint256(removeSeed));

        assertGt(s.x, 0);
        assertGt(s.y, 0);
        assertGt(s.L, 0);
    }

    function testFuzz_stateful_differential_mixed_operations(
        uint64 sx,
        uint64 sy,
        uint8 op1,
        uint96 seed1,
        uint8 op2,
        uint96 seed2,
        uint8 op3,
        uint96 seed3
    ) public {
        uint256 x0 = bound(uint256(sx), 1_000, 10**8);
        uint256 y0 = bound(uint256(sy), 1_000, 10**8);
        ModelState memory s = _seedPool(x0, y0);

        s = _executeStep(s, op1, seed1);
        s = _executeStep(s, op2, seed2);
        s = _executeStep(s, op3, seed3);

        _assertContractMatches(s);
        assertGt(s.x, 0);
        assertGt(s.y, 0);
        assertGt(s.L, 0);
    }
}
