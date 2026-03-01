// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {IERC20Minimal} from "./interfaces/IERC20Minimal.sol";

/// @notice ERC20-backed CPAMM variant with internal reserve accounting and LP shares.
/// @dev This module is test-validated and intentionally separate from the Lean-refined core contract.
contract CPAMMTokenized {
    IERC20Minimal public immutable tokenX;
    IERC20Minimal public immutable tokenY;

    uint256 public reserveX;
    uint256 public reserveY;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    uint256 public immutable feeNumerator;
    uint256 public immutable feeDenominator;
    uint256 private _status;
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    event LiquidityAdded(
        address indexed provider, uint256 dx, uint256 dy, uint256 shares, uint256 reserveX, uint256 reserveY, uint256 totalSupply
    );
    event LiquidityRemoved(
        address indexed provider, uint256 dx, uint256 dy, uint256 shares, uint256 reserveX, uint256 reserveY, uint256 totalSupply
    );
    event SwapXForY(address indexed trader, uint256 dxIn, uint256 dyOut, uint256 reserveX, uint256 reserveY);
    event SwapYForX(address indexed trader, uint256 dyIn, uint256 dxOut, uint256 reserveX, uint256 reserveY);

    constructor(IERC20Minimal _tokenX, IERC20Minimal _tokenY, uint256 _feeNumerator, uint256 _feeDenominator) {
        require(address(_tokenX) != address(0) && address(_tokenY) != address(0), "zero token");
        require(address(_tokenX) != address(_tokenY), "identical token");
        require(_feeDenominator > 0, "fee denominator zero");
        require(_feeNumerator < _feeDenominator, "invalid fee");

        tokenX = _tokenX;
        tokenY = _tokenY;
        feeNumerator = _feeNumerator;
        feeDenominator = _feeDenominator;
        _status = _NOT_ENTERED;
    }

    modifier nonReentrant() {
        require(_status != _ENTERED, "reentrancy");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }

    function addLiquidity(uint256 dx, uint256 dy) external nonReentrant returns (uint256 shares) {
        require(dx > 0 && dy > 0, "zero input");
        _assertReservesMatchBalances();

        if (totalSupply == 0) {
            shares = dx;
        } else {
            require(dx * reserveY == dy * reserveX, "not proportional");
            shares = (totalSupply * dx) / reserveX;
        }
        require(shares > 0, "zero shares");

        reserveX += dx;
        reserveY += dy;
        totalSupply += shares;
        balanceOf[msg.sender] += shares;

        _pullExact(tokenX, msg.sender, dx);
        _pullExact(tokenY, msg.sender, dy);
        _assertReservesMatchBalances();
        emit LiquidityAdded(msg.sender, dx, dy, shares, reserveX, reserveY, totalSupply);
    }

    function removeLiquidity(uint256 shares) external nonReentrant returns (uint256 dx, uint256 dy) {
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
        emit LiquidityRemoved(msg.sender, dx, dy, shares, reserveX, reserveY, totalSupply);
    }

    function swapXforY(uint256 dx) external nonReentrant returns (uint256 dy) {
        require(dx > 0, "zero input");
        _assertReservesMatchBalances();

        uint256 dxEff = (dx * (feeDenominator - feeNumerator)) / feeDenominator;
        dy = (reserveY * dxEff) / (reserveX + dxEff);
        require(dy > 0, "insufficient output");
        require(dy < reserveY, "empty reserve");

        reserveX += dx;
        reserveY -= dy;
        _pullExact(tokenX, msg.sender, dx);
        _pushExact(tokenY, msg.sender, dy);
        _assertReservesMatchBalances();
        emit SwapXForY(msg.sender, dx, dy, reserveX, reserveY);
    }

    function swapYforX(uint256 dy) external nonReentrant returns (uint256 dx) {
        require(dy > 0, "zero input");
        _assertReservesMatchBalances();

        uint256 dyEff = (dy * (feeDenominator - feeNumerator)) / feeDenominator;
        dx = (reserveX * dyEff) / (reserveY + dyEff);
        require(dx > 0, "insufficient output");
        require(dx < reserveX, "empty reserve");

        reserveY += dy;
        reserveX -= dx;
        _pullExact(tokenY, msg.sender, dy);
        _pushExact(tokenX, msg.sender, dx);
        _assertReservesMatchBalances();
        emit SwapYForX(msg.sender, dy, dx, reserveX, reserveY);
    }

    function _assertReservesMatchBalances() internal view {
        uint256 balX = tokenX.balanceOf(address(this));
        require(reserveX >= balX, "reserveX mismatch");
        require(reserveX <= balX, "reserveX mismatch");

        uint256 balY = tokenY.balanceOf(address(this));
        require(reserveY >= balY, "reserveY mismatch");
        require(reserveY <= balY, "reserveY mismatch");
    }

    function _pullExact(IERC20Minimal token, address from, uint256 amount) internal {
        uint256 beforeBal = token.balanceOf(address(this));
        _safeTransferFrom(token, from, address(this), amount);
        uint256 afterBal = token.balanceOf(address(this));
        require(afterBal >= beforeBal, "balance regression");
        uint256 delta = afterBal - beforeBal;
        require(delta >= amount, "fee-on-transfer unsupported");
        require(delta <= amount, "fee-on-transfer unsupported");
    }

    function _pushExact(IERC20Minimal token, address to, uint256 amount) internal {
        uint256 beforeBal = token.balanceOf(address(this));
        _safeTransfer(token, to, amount);
        uint256 afterBal = token.balanceOf(address(this));
        require(beforeBal >= afterBal, "balance growth");
        uint256 delta = beforeBal - afterBal;
        require(delta >= amount, "fee-on-transfer unsupported");
        require(delta <= amount, "fee-on-transfer unsupported");
    }

    function _safeTransfer(IERC20Minimal token, address to, uint256 amount) internal {
        require(token.transfer(to, amount), "transfer failed");
    }

    function _safeTransferFrom(IERC20Minimal token, address from, address to, uint256 amount) internal {
        require(token.transferFrom(from, to, amount), "transferFrom failed");
    }
}
