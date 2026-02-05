import pytest
from unittest.mock import AsyncMock
from engine.risk_manager import RiskManager
from config import Config

@pytest.mark.asyncio
async def test_risk_manager_valid_trade():
    mock_provider = AsyncMock(return_value={'NetLiquidation': 100000})
    rm = RiskManager(mock_provider)

    # Trade: Buy 100 shares @ $100. Value = $10,000 (10% of 100k).
    # Stop Loss @ $98. Risk = $2 * 100 = $200 (0.2% of 100k).
    # All checks should pass.
    valid, msg = await rm.validate_trade('AAPL', 100, 100, 'BUY', stop_loss=98)
    assert valid is True
    assert msg == "Trade Approved"

@pytest.mark.asyncio
async def test_risk_manager_position_size_too_big():
    mock_provider = AsyncMock(return_value={'NetLiquidation': 100000})
    rm = RiskManager(mock_provider)

    # Trade: Buy 200 shares @ $100. Value = $20,000 (20% of 100k).
    # Max allowed is 10%. Should Fail.
    valid, msg = await rm.validate_trade('AAPL', 200, 100, 'BUY', stop_loss=98)
    assert valid is False
    assert "exceeds max allowed" in msg

@pytest.mark.asyncio
async def test_risk_manager_missing_stop_loss():
    mock_provider = AsyncMock(return_value={'NetLiquidation': 100000})
    rm = RiskManager(mock_provider)

    Config.REQUIRE_STOP_LOSS = True
    valid, msg = await rm.validate_trade('AAPL', 10, 100, 'BUY', stop_loss=None)
    assert valid is False
    assert "Stop Loss is REQUIRED" in msg

@pytest.mark.asyncio
async def test_risk_manager_risk_too_high():
    mock_provider = AsyncMock(return_value={'NetLiquidation': 100000})
    rm = RiskManager(mock_provider)

    # Trade: Buy 100 shares @ $100.
    # Stop Loss @ $70. Risk = $30 * 100 = $3000.
    # Max Risk = 2% of 100k = $2000.
    # Should Fail.
    valid, msg = await rm.validate_trade('AAPL', 100, 100, 'BUY', stop_loss=70)
    assert valid is False
    assert "Risk 3000.00 exceeds max allowed" in msg
