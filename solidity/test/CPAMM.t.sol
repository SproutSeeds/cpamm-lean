// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Test} from "forge-std/Test.sol";
import {CPAMM} from "../src/CPAMM.sol";

contract CPAMMTest is Test {
    CPAMM internal cpamm;
    address internal alice = address(0xA11CE);

    function setUp() public {
        cpamm = new CPAMM(3, 1000);
    }

    function test_addLiquidity_increases_reserves() public {
        uint256 shares0 = cpamm.addLiquidity(1000, 1000);
        assertEq(shares0, 1000);
        assertEq(cpamm.reserveX(), 1000);
        assertEq(cpamm.reserveY(), 1000);
        assertEq(cpamm.totalSupply(), 1000);
        assertEq(cpamm.balanceOf(address(this)), 1000);

        uint256 shares1 = cpamm.addLiquidity(500, 500);
        assertEq(shares1, 500);
        assertEq(cpamm.reserveX(), 1500);
        assertEq(cpamm.reserveY(), 1500);
        assertEq(cpamm.totalSupply(), 1500);
        assertEq(cpamm.balanceOf(address(this)), 1500);
    }

    function test_removeLiquidity_proportional() public {
        cpamm.addLiquidity(1000, 2000);
        uint256 supplyBefore = cpamm.totalSupply();
        uint256 xBefore = cpamm.reserveX();
        uint256 yBefore = cpamm.reserveY();

        (uint256 dx, uint256 dy) = cpamm.removeLiquidity(250);
        assertEq(dx, 250);
        assertEq(dy, 500);
        assertEq(cpamm.reserveX(), 750);
        assertEq(cpamm.reserveY(), 1500);
        assertEq(cpamm.totalSupply(), 750);

        assertEq(dx * supplyBefore, xBefore * 250);
        assertEq(dy * supplyBefore, yBefore * 250);
    }

    function test_swap_product_nondecreasing() public {
        cpamm.addLiquidity(1_000_000, 1_000_000);
        uint256 kBefore = cpamm.reserveX() * cpamm.reserveY();

        cpamm.swapXforY(100_000);

        uint256 kAfter = cpamm.reserveX() * cpamm.reserveY();
        assertGe(kAfter, kBefore);
    }

    function test_swap_output_bounded() public {
        cpamm.addLiquidity(1_000_000, 1_000_000);
        uint256 yBefore = cpamm.reserveY();

        uint256 dy = cpamm.swapXforY(10_000);

        assertLt(dy, yBefore);
        assertEq(cpamm.reserveY(), yBefore - dy);
    }

    function testFuzz_swap_sequence(uint96 seed, uint96 a, uint96 b, uint96 c) public {
        uint256 base = bound(uint256(seed), 1_000_000, 10**24);
        cpamm.addLiquidity(base, base);

        uint256 minX1 = (cpamm.reserveX() / 1_000_000) + 2;
        uint256 maxX1 = cpamm.reserveX() / 4;
        uint256 dx1 = bound(uint256(a), minX1, maxX1);
        cpamm.swapXforY(dx1);
        assertGt(cpamm.reserveX(), 0);
        assertGt(cpamm.reserveY(), 0);

        uint256 minY2 = (cpamm.reserveY() / 1_000_000) + 2;
        uint256 maxY2 = cpamm.reserveY() / 4;
        uint256 dy2 = bound(uint256(b), minY2, maxY2);
        cpamm.swapYforX(dy2);
        assertGt(cpamm.reserveX(), 0);
        assertGt(cpamm.reserveY(), 0);

        uint256 minX3 = (cpamm.reserveX() / 1_000_000) + 2;
        uint256 maxX3 = cpamm.reserveX() / 4;
        uint256 dx3 = bound(uint256(c), minX3, maxX3);
        cpamm.swapXforY(dx3);
        assertGt(cpamm.reserveX(), 0);
        assertGt(cpamm.reserveY(), 0);
    }

    function testFuzz_add_remove_roundtrip(uint96 xSeed) public {
        vm.startPrank(alice);
        cpamm.addLiquidity(1_000_000, 1_000_000);
        vm.stopPrank();

        uint256 dx = bound(uint256(xSeed), 10, 10**18);
        uint256 shares = cpamm.addLiquidity(dx, dx);
        assertEq(shares, dx);

        (uint256 outX, uint256 outY) = cpamm.removeLiquidity(shares);
        assertEq(outX, dx);
        assertEq(outY, dx);
        assertEq(cpamm.balanceOf(address(this)), 0);
    }

    function test_edge_tiny_reserves() public {
        cpamm.addLiquidity(1, 1);
        vm.expectRevert("insufficient output");
        cpamm.swapXforY(3);
        assertEq(cpamm.reserveX(), 1);
        assertEq(cpamm.reserveY(), 1);
    }

    function test_edge_large_values() public {
        uint256 large = type(uint256).max / 4;
        cpamm.addLiquidity(large, large);

        uint256 dy = cpamm.swapXforY(3);
        assertGt(dy, 0);
        assertGt(cpamm.reserveX(), 0);
        assertGt(cpamm.reserveY(), 0);
        assertEq(cpamm.reserveX(), large + 3);
    }
}
