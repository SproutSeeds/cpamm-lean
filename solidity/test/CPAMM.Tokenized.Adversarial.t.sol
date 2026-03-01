// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Test} from "forge-std/Test.sol";
import {CPAMMTokenized} from "../src/CPAMMTokenized.sol";
import {IERC20Minimal} from "../src/interfaces/IERC20Minimal.sol";

contract AdvMockERC20 {
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

contract FalseTransferFromERC20 is AdvMockERC20 {
    constructor(string memory _name, string memory _symbol) AdvMockERC20(_name, _symbol) {}

    function transferFrom(address, address, uint256) external pure override returns (bool) {
        return false;
    }
}

contract NoOpTransferFromERC20 is AdvMockERC20 {
    constructor(string memory _name, string memory _symbol) AdvMockERC20(_name, _symbol) {}

    function transferFrom(address from, address, uint256 amount) external override returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= amount, "insufficient allowance");
        if (allowed != type(uint256).max) {
            allowance[from][msg.sender] = allowed - amount;
        }
        return true;
    }
}

contract InflationaryERC20 is AdvMockERC20 {
    uint256 public immutable bonus;

    constructor(string memory _name, string memory _symbol, uint256 _bonus) AdvMockERC20(_name, _symbol) {
        bonus = _bonus;
    }

    function _transfer(address from, address to, uint256 amount) internal override {
        require(balanceOf[from] >= amount, "insufficient balance");
        balanceOf[from] -= amount;
        balanceOf[to] += amount + bonus;
        totalSupply += bonus;
    }
}

contract FalseTransferERC20 is AdvMockERC20 {
    constructor(string memory _name, string memory _symbol) AdvMockERC20(_name, _symbol) {}

    function transfer(address to, uint256 amount) external override returns (bool) {
        _transfer(msg.sender, to, amount);
        return false;
    }
}

contract RebaseableERC20 is AdvMockERC20 {
    constructor(string memory _name, string memory _symbol) AdvMockERC20(_name, _symbol) {}

    function rebase(address to, uint256 amount) external {
        totalSupply += amount;
        balanceOf[to] += amount;
    }
}

contract CPAMMTokenizedAdversarialTest is Test {
    uint256 internal constant BASE = 1_000_000;

    function _deploy(AdvMockERC20 tokenX, AdvMockERC20 tokenY) internal returns (CPAMMTokenized cpamm) {
        cpamm = new CPAMMTokenized(IERC20Minimal(address(tokenX)), IERC20Minimal(address(tokenY)), 3, 1000);
        tokenX.mint(address(this), 10 * BASE);
        tokenY.mint(address(this), 10 * BASE);
        tokenX.approve(address(cpamm), type(uint256).max);
        tokenY.approve(address(cpamm), type(uint256).max);
    }

    function test_rejectsFalseTransferFromToken() public {
        FalseTransferFromERC20 tokenX = new FalseTransferFromERC20("Bad X", "bX");
        AdvMockERC20 tokenY = new AdvMockERC20("Token Y", "Y");
        CPAMMTokenized cpamm = _deploy(tokenX, tokenY);

        vm.expectRevert("transferFrom failed");
        cpamm.addLiquidity(BASE, BASE);
    }

    function test_rejectsNoOpTransferFromToken() public {
        NoOpTransferFromERC20 tokenX = new NoOpTransferFromERC20("NoOp X", "nX");
        AdvMockERC20 tokenY = new AdvMockERC20("Token Y", "Y");
        CPAMMTokenized cpamm = _deploy(tokenX, tokenY);

        vm.expectRevert("fee-on-transfer unsupported");
        cpamm.addLiquidity(BASE, BASE);
    }

    function test_rejectsInflationaryTransferToken() public {
        InflationaryERC20 tokenX = new InflationaryERC20("Inflate X", "iX", 1);
        AdvMockERC20 tokenY = new AdvMockERC20("Token Y", "Y");
        CPAMMTokenized cpamm = _deploy(tokenX, tokenY);

        vm.expectRevert("fee-on-transfer unsupported");
        cpamm.addLiquidity(BASE, BASE);
    }

    function test_rejectsFalseTransferOnOutputPath() public {
        AdvMockERC20 tokenX = new AdvMockERC20("Token X", "X");
        FalseTransferERC20 tokenY = new FalseTransferERC20("False Y", "fY");
        CPAMMTokenized cpamm = _deploy(tokenX, tokenY);

        cpamm.addLiquidity(BASE, BASE);

        vm.expectRevert("transfer failed");
        cpamm.swapXforY(10_000);
    }

    function test_revertsOnExternalBalanceDrift() public {
        RebaseableERC20 tokenX = new RebaseableERC20("Rebase X", "rX");
        AdvMockERC20 tokenY = new AdvMockERC20("Token Y", "Y");
        CPAMMTokenized cpamm = _deploy(tokenX, tokenY);

        cpamm.addLiquidity(BASE, BASE);
        tokenX.rebase(address(cpamm), 1);

        vm.expectRevert("reserveX mismatch");
        cpamm.swapXforY(10_000);
    }
}
