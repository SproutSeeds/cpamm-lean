// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {StdInvariant} from "forge-std/StdInvariant.sol";
import {Test} from "forge-std/Test.sol";
import {CPAMM} from "../src/CPAMM.sol";

contract CPAMMHandler {
    CPAMM internal immutable cpamm;

    constructor(CPAMM _cpamm) {
        cpamm = _cpamm;
        cpamm.addLiquidity(1_000_000, 1_000_000);
    }

    function _gcd(uint256 a, uint256 b) internal pure returns (uint256) {
        while (b != 0) {
            uint256 t = a % b;
            a = b;
            b = t;
        }
        return a;
    }

    function _bound(uint256 seed, uint256 min, uint256 max) internal pure returns (uint256) {
        if (seed < min) {
            return min + (seed % (max - min + 1));
        }
        if (seed > max) {
            return min + (seed % (max - min + 1));
        }
        return seed;
    }

    function addLiquidity(uint96 seed) external {
        uint256 x = cpamm.reserveX();
        uint256 y = cpamm.reserveY();
        if (x == 0 || y == 0) {
            return;
        }

        uint256 g = _gcd(x, y);
        uint256 unitX = x / g;
        uint256 unitY = y / g;
        uint256 mul = _bound(uint256(seed), 1, 4);
        uint256 dx = unitX * mul;
        uint256 dy = unitY * mul;

        if (dx != 0 && y > type(uint256).max / dx) {
            return;
        }
        if (dy != 0 && x > type(uint256).max / dy) {
            return;
        }
        uint256 supply = cpamm.totalSupply();
        if (supply != 0) {
            if (dx != 0 && supply > type(uint256).max / dx) {
                return;
            }
            uint256 minted = (supply * dx) / x;
            if (minted == 0) {
                return;
            }
        }

        cpamm.addLiquidity(dx, dy);
    }

    function removeLiquidity(uint96 seed) external {
        uint256 bal = cpamm.balanceOf(address(this));
        uint256 supply = cpamm.totalSupply();
        if (bal <= 1 || supply <= 1) {
            return;
        }

        uint256 maxShares = bal;
        if (maxShares >= supply) {
            maxShares = supply - 1;
        }
        if (maxShares == 0) {
            return;
        }

        uint256 shares = _bound(uint256(seed), 1, maxShares);
        cpamm.removeLiquidity(shares);
    }

    function swapXforY(uint96 seed) external {
        uint256 x = cpamm.reserveX();
        uint256 y = cpamm.reserveY();
        uint256 maxIn = x / 5;
        if (y == 0 || maxIn < 2) {
            return;
        }

        uint256 dx = _bound(uint256(seed), 2, maxIn);
        uint256 dxEff = (dx * (cpamm.feeDenominator() - cpamm.feeNumerator())) / cpamm.feeDenominator();
        uint256 out = (y * dxEff) / (x + dxEff);
        if (out == 0 || out >= y) {
            return;
        }

        cpamm.swapXforY(dx);
    }

    function swapYforX(uint96 seed) external {
        uint256 x = cpamm.reserveX();
        uint256 y = cpamm.reserveY();
        uint256 maxIn = y / 5;
        if (x == 0 || maxIn < 2) {
            return;
        }

        uint256 dy = _bound(uint256(seed), 2, maxIn);
        uint256 dyEff = (dy * (cpamm.feeDenominator() - cpamm.feeNumerator())) / cpamm.feeDenominator();
        uint256 out = (x * dyEff) / (y + dyEff);
        if (out == 0 || out >= x) {
            return;
        }

        cpamm.swapYforX(dy);
    }
}

contract CPAMMInvariantTest is StdInvariant, Test {
    CPAMM internal cpamm;
    CPAMMHandler internal handler;

    function setUp() public {
        cpamm = new CPAMM(3, 1000);
        handler = new CPAMMHandler(cpamm);

        bytes4[] memory selectors = new bytes4[](4);
        selectors[0] = CPAMMHandler.addLiquidity.selector;
        selectors[1] = CPAMMHandler.removeLiquidity.selector;
        selectors[2] = CPAMMHandler.swapXforY.selector;
        selectors[3] = CPAMMHandler.swapYforX.selector;
        targetSelector(FuzzSelector({addr: address(handler), selectors: selectors}));
        targetContract(address(handler));
    }

    function invariant_reservesStayPositive() public view {
        assertGt(cpamm.reserveX(), 0, "reserveX must stay positive");
        assertGt(cpamm.reserveY(), 0, "reserveY must stay positive");
    }

    function invariant_totalSupplyStaysPositive() public view {
        assertGt(cpamm.totalSupply(), 0, "totalSupply must stay positive");
    }

    function invariant_lpAccounting_singleActor() public view {
        assertEq(cpamm.totalSupply(), cpamm.balanceOf(address(handler)), "single-actor LP accounting broken");
    }

    function invariant_feeParamsImmutable() public view {
        assertEq(cpamm.feeNumerator(), 3, "fee numerator changed");
        assertEq(cpamm.feeDenominator(), 1000, "fee denominator changed");
    }
}
