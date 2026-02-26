// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {CPAMM} from "../src/CPAMM.sol";

contract CPAMMDifferentialTest is Test {
    uint256 internal constant FEE_NUM = 3;
    uint256 internal constant FEE_DEN = 1000;
    CPAMM internal cpamm;

    function setUp() public {
        cpamm = new CPAMM(FEE_NUM, FEE_DEN);
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
}
