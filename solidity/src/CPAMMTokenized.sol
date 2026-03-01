// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {IERC20} from "forge-std/interfaces/IERC20.sol";

/// @notice ERC20-backed CPAMM variant with internal reserve accounting and LP shares.
/// @dev This module is test-validated and intentionally separate from the Lean-refined core contract.
contract CPAMMTokenized {
    IERC20 public immutable tokenX;
    IERC20 public immutable tokenY;

    uint256 public reserveX;
    uint256 public reserveY;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    uint256 public immutable feeNumerator;
    uint256 public immutable feeDenominator;

    constructor(IERC20 _tokenX, IERC20 _tokenY, uint256 _feeNumerator, uint256 _feeDenominator) {
        require(address(_tokenX) != address(0) && address(_tokenY) != address(0), "zero token");
        require(address(_tokenX) != address(_tokenY), "identical token");
        require(_feeDenominator > 0, "fee denominator zero");
        require(_feeNumerator < _feeDenominator, "invalid fee");

        tokenX = _tokenX;
        tokenY = _tokenY;
        feeNumerator = _feeNumerator;
        feeDenominator = _feeDenominator;
    }

    function addLiquidity(uint256 dx, uint256 dy) external returns (uint256 shares) {
        require(dx > 0 && dy > 0, "zero input");
        _assertReservesMatchBalances();

        if (totalSupply == 0) {
            shares = dx;
        } else {
            require(dx * reserveY == dy * reserveX, "not proportional");
            shares = (totalSupply * dx) / reserveX;
        }
        require(shares > 0, "zero shares");

        _pullExact(tokenX, msg.sender, dx);
        _pullExact(tokenY, msg.sender, dy);

        reserveX += dx;
        reserveY += dy;
        totalSupply += shares;
        balanceOf[msg.sender] += shares;
        _assertReservesMatchBalances();
    }

    function removeLiquidity(uint256 shares) external returns (uint256 dx, uint256 dy) {
        require(shares > 0, "zero shares");
        require(shares <= balanceOf[msg.sender], "insufficient shares");
        require(shares < totalSupply, "must leave liquidity");
        _assertReservesMatchBalances();

        dx = (reserveX * shares) / totalSupply;
        dy = (reserveY * shares) / totalSupply;

        reserveX -= dx;
        reserveY -= dy;
        totalSupply -= shares;
        balanceOf[msg.sender] -= shares;

        _pushExact(tokenX, msg.sender, dx);
        _pushExact(tokenY, msg.sender, dy);
        _assertReservesMatchBalances();
    }

    function swapXforY(uint256 dx) external returns (uint256 dy) {
        require(dx > 0, "zero input");
        _assertReservesMatchBalances();

        _pullExact(tokenX, msg.sender, dx);

        uint256 dxEff = (dx * (feeDenominator - feeNumerator)) / feeDenominator;
        dy = (reserveY * dxEff) / (reserveX + dxEff);
        require(dy > 0, "insufficient output");
        require(dy < reserveY, "empty reserve");

        reserveX += dx;
        reserveY -= dy;

        _pushExact(tokenY, msg.sender, dy);
        _assertReservesMatchBalances();
    }

    function swapYforX(uint256 dy) external returns (uint256 dx) {
        require(dy > 0, "zero input");
        _assertReservesMatchBalances();

        _pullExact(tokenY, msg.sender, dy);

        uint256 dyEff = (dy * (feeDenominator - feeNumerator)) / feeDenominator;
        dx = (reserveX * dyEff) / (reserveY + dyEff);
        require(dx > 0, "insufficient output");
        require(dx < reserveX, "empty reserve");

        reserveY += dy;
        reserveX -= dx;

        _pushExact(tokenX, msg.sender, dx);
        _assertReservesMatchBalances();
    }

    function _assertReservesMatchBalances() internal view {
        require(reserveX == tokenX.balanceOf(address(this)), "reserveX mismatch");
        require(reserveY == tokenY.balanceOf(address(this)), "reserveY mismatch");
    }

    function _pullExact(IERC20 token, address from, uint256 amount) internal {
        uint256 beforeBal = token.balanceOf(address(this));
        _safeTransferFrom(token, from, address(this), amount);
        uint256 afterBal = token.balanceOf(address(this));
        require(afterBal == beforeBal + amount, "fee-on-transfer unsupported");
    }

    function _pushExact(IERC20 token, address to, uint256 amount) internal {
        uint256 beforeBal = token.balanceOf(address(this));
        _safeTransfer(token, to, amount);
        uint256 afterBal = token.balanceOf(address(this));
        require(beforeBal == afterBal + amount, "fee-on-transfer unsupported");
    }

    function _safeTransfer(IERC20 token, address to, uint256 amount) internal {
        (bool ok, bytes memory data) = address(token).call(abi.encodeCall(IERC20.transfer, (to, amount)));
        require(ok && (data.length == 0 || abi.decode(data, (bool))), "transfer failed");
    }

    function _safeTransferFrom(IERC20 token, address from, address to, uint256 amount) internal {
        (bool ok, bytes memory data) = address(token).call(abi.encodeCall(IERC20.transferFrom, (from, to, amount)));
        require(ok && (data.length == 0 || abi.decode(data, (bool))), "transferFrom failed");
    }
}
