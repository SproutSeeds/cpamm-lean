// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

contract CPAMM {
    uint256 public reserveX;
    uint256 public reserveY;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    uint256 public immutable feeNumerator;
    uint256 public immutable feeDenominator;

    constructor(uint256 _feeNumerator, uint256 _feeDenominator) {
        require(_feeDenominator > 0, "fee denominator zero");
        require(_feeNumerator < _feeDenominator, "invalid fee");
        feeNumerator = _feeNumerator;
        feeDenominator = _feeDenominator;
    }

    function addLiquidity(uint256 dx, uint256 dy) external returns (uint256 shares) {
        require(dx > 0 && dy > 0, "zero input");

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
    }

    function removeLiquidity(uint256 shares) external returns (uint256 dx, uint256 dy) {
        require(shares > 0, "zero shares");
        require(shares <= balanceOf[msg.sender], "insufficient shares");
        require(shares < totalSupply, "must leave liquidity");

        dx = (reserveX * shares) / totalSupply;
        dy = (reserveY * shares) / totalSupply;

        reserveX -= dx;
        reserveY -= dy;
        totalSupply -= shares;
        balanceOf[msg.sender] -= shares;
    }

    function swapXforY(uint256 dx) external returns (uint256 dy) {
        require(dx > 0, "zero input");
        uint256 dxEff = (dx * (feeDenominator - feeNumerator)) / feeDenominator;
        dy = (reserveY * dxEff) / (reserveX + dxEff);
        require(dy > 0, "insufficient output");
        require(dy < reserveY, "empty reserve");

        reserveX += dx;
        reserveY -= dy;
    }

    function swapYforX(uint256 dy) external returns (uint256 dx) {
        require(dy > 0, "zero input");
        uint256 dyEff = (dy * (feeDenominator - feeNumerator)) / feeDenominator;
        dx = (reserveX * dyEff) / (reserveY + dyEff);
        require(dx > 0, "insufficient output");
        require(dx < reserveX, "empty reserve");

        reserveY += dy;
        reserveX -= dx;
    }
}
