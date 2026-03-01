// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Test} from "forge-std/Test.sol";
import {CPAMMTokenized} from "../src/CPAMMTokenized.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

contract MockERC20 {
    string public name;
    string public symbol;
    uint8 public immutable decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    function mint(address to, uint256 amount) external {
        totalSupply += amount;
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external virtual returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external virtual returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= amount, "insufficient allowance");
        if (allowed != type(uint256).max) {
            allowance[from][msg.sender] = allowed - amount;
        }
        _transfer(from, to, amount);
        return true;
    }

    function _transfer(address from, address to, uint256 amount) internal virtual {
        require(balanceOf[from] >= amount, "insufficient balance");
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
    }
}

contract FeeOnTransferMockERC20 is MockERC20 {
    uint256 public immutable feeBps;

    constructor(string memory _name, string memory _symbol, uint256 _feeBps) MockERC20(_name, _symbol) {
        require(_feeBps < 10_000, "invalid fee bps");
        feeBps = _feeBps;
    }

    function _transfer(address from, address to, uint256 amount) internal override {
        require(balanceOf[from] >= amount, "insufficient balance");
        uint256 fee = (amount * feeBps) / 10_000;
        uint256 net = amount - fee;

        balanceOf[from] -= amount;
        balanceOf[to] += net;
        totalSupply -= fee;
    }
}

contract CPAMMTokenizedTest is Test {
    MockERC20 internal tokenX;
    MockERC20 internal tokenY;
    CPAMMTokenized internal cpamm;
    address internal alice = address(0xA11CE);

    function setUp() public {
        tokenX = new MockERC20("Token X", "X");
        tokenY = new MockERC20("Token Y", "Y");
        cpamm = new CPAMMTokenized(IERC20(address(tokenX)), IERC20(address(tokenY)), 3, 1000);

        tokenX.mint(address(this), 10**24);
        tokenY.mint(address(this), 10**24);
        tokenX.mint(alice, 10**24);
        tokenY.mint(alice, 10**24);

        tokenX.approve(address(cpamm), type(uint256).max);
        tokenY.approve(address(cpamm), type(uint256).max);
        vm.startPrank(alice);
        tokenX.approve(address(cpamm), type(uint256).max);
        tokenY.approve(address(cpamm), type(uint256).max);
        vm.stopPrank();
    }

    function _assertReserveSync() internal view {
        assertEq(cpamm.reserveX(), tokenX.balanceOf(address(cpamm)), "reserveX != tokenX balance");
        assertEq(cpamm.reserveY(), tokenY.balanceOf(address(cpamm)), "reserveY != tokenY balance");
    }

    function _gcd(uint256 a, uint256 b) internal pure returns (uint256) {
        while (b != 0) {
            uint256 t = a % b;
            a = b;
            b = t;
        }
        return a;
    }

    function test_addLiquidity_reserveSync() public {
        uint256 shares = cpamm.addLiquidity(1_000, 1_000);
        assertEq(shares, 1_000);
        _assertReserveSync();
        assertEq(cpamm.balanceOf(address(this)), 1_000);
    }

    function test_swapXforY_reserveSync() public {
        cpamm.addLiquidity(1_000_000, 1_000_000);
        uint256 yBefore = tokenY.balanceOf(address(this));
        uint256 out = cpamm.swapXforY(10_000);
        assertGt(out, 0);
        assertEq(tokenY.balanceOf(address(this)), yBefore + out);
        _assertReserveSync();
    }

    function test_swapYforX_reserveSync() public {
        cpamm.addLiquidity(1_000_000, 1_000_000);
        uint256 xBefore = tokenX.balanceOf(address(this));
        uint256 out = cpamm.swapYforX(10_000);
        assertGt(out, 0);
        assertEq(tokenX.balanceOf(address(this)), xBefore + out);
        _assertReserveSync();
    }

    function test_removeLiquidity_reserveSync() public {
        cpamm.addLiquidity(1_000_000, 1_000_000);
        (uint256 outX, uint256 outY) = cpamm.removeLiquidity(100_000);
        assertGt(outX, 0);
        assertGt(outY, 0);
        _assertReserveSync();
    }

    function test_feeOnTransferToken_rejected() public {
        FeeOnTransferMockERC20 feeX = new FeeOnTransferMockERC20("Fee X", "fX", 100);
        MockERC20 plainY = new MockERC20("Plain Y", "pY");
        CPAMMTokenized badPool = new CPAMMTokenized(IERC20(address(feeX)), IERC20(address(plainY)), 3, 1000);

        feeX.mint(address(this), 1_000_000);
        plainY.mint(address(this), 1_000_000);
        feeX.approve(address(badPool), type(uint256).max);
        plainY.approve(address(badPool), type(uint256).max);

        vm.expectRevert("fee-on-transfer unsupported");
        badPool.addLiquidity(100_000, 100_000);
    }

    function testFuzz_tokenized_multiStep_reserveSync(uint96 a, uint96 b, uint96 c, uint96 d) public {
        uint256 base = 1_000_000;
        cpamm.addLiquidity(base, base);

        uint256 minX = (cpamm.reserveX() / 1_000_000) + 2;
        uint256 maxX = cpamm.reserveX() / 5;
        uint256 dx = bound(uint256(a), minX, maxX);
        cpamm.swapXforY(dx);
        _assertReserveSync();

        uint256 minY = (cpamm.reserveY() / 1_000_000) + 2;
        uint256 maxY = cpamm.reserveY() / 5;
        uint256 dy = bound(uint256(b), minY, maxY);
        cpamm.swapYforX(dy);
        _assertReserveSync();

        uint256 x = cpamm.reserveX();
        uint256 y = cpamm.reserveY();
        uint256 g = _gcd(x, y);
        uint256 unitX = x / g;
        uint256 unitY = y / g;
        uint256 scale = bound(uint256(c), 1, 50);
        cpamm.addLiquidity(unitX * scale, unitY * scale);
        _assertReserveSync();

        uint256 shares = bound(uint256(d), 1, cpamm.balanceOf(address(this)) / 2);
        cpamm.removeLiquidity(shares);
        _assertReserveSync();
    }
}
