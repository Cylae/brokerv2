import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from engine.risk_manager import RiskManager
from engine.models import AccountSummary, RiskCheck

@pytest.fixture
def mock_provider():
    return AsyncMock(return_value=AccountSummary(
        net_liquidation=100000.0,
        total_cash=50000.0
    ))

@pytest.fixture
def mock_config():
    with patch('engine.risk_manager.Config') as mock_cfg:
        mock_cfg.MAX_POSITION_SIZE_PCT = 0.10
        mock_cfg.MAX_RISK_PER_TRADE_PCT = 0.02
        mock_cfg.REQUIRE_STOP_LOSS = True
        yield mock_cfg

@pytest.mark.asyncio
async def test_risk_manager_valid_trade(mock_provider, mock_config):
    rm = RiskManager(mock_provider)

    # Trade: Buy 100 shares @ $100. Value = $10,000 (10% of 100k).
    # Stop Loss @ $98. Risk = $2 * 100 = $200 (0.2% of 100k).
    check = await rm.validate_trade('AAPL', 100, 100, 'BUY', stop_loss=98)
    assert check.passed is True
    assert check.reason == "Trade Approved"

@pytest.mark.asyncio
async def test_risk_manager_position_size_too_big(mock_provider, mock_config):
    rm = RiskManager(mock_provider)

    # Trade: Buy 200 shares @ $100. Value = $20,000 (20% of 100k).
    # Max allowed is 10%. Should Fail.
    check = await rm.validate_trade('AAPL', 200, 100, 'BUY', stop_loss=98)
    assert check.passed is False
    assert "exceeds max allowed" in check.reason

@pytest.mark.asyncio
async def test_risk_manager_missing_stop_loss(mock_provider, mock_config):
    rm = RiskManager(mock_provider)

    # Mock Config directly or assume default REQUIRE_STOP_LOSS is True
    check = await rm.validate_trade('AAPL', 10, 100, 'BUY', stop_loss=None)
    assert check.passed is False
    assert "Stop Loss is REQUIRED" in check.reason

@pytest.mark.asyncio
async def test_risk_manager_risk_too_high(mock_provider, mock_config):
    rm = RiskManager(mock_provider)

    # Trade: Buy 100 shares @ $100.
    # Stop Loss @ $70. Risk = $30 * 100 = $3000.
    # Max Risk = 2% of 100k = $2000.
    check = await rm.validate_trade('AAPL', 100, 100, 'BUY', stop_loss=70)
    assert check.passed is False
    assert "Risk 3000.00 exceeds max allowed" in check.reason

@pytest.mark.asyncio
async def test_risk_manager_caching(mock_provider):
    rm = RiskManager(mock_provider)

    # Call once
    data1 = await rm._get_account_data()
    # Call twice
    data2 = await rm._get_account_data()

    assert mock_provider.call_count == 1
    assert data1 is data2

@pytest.mark.asyncio
async def test_risk_manager_caching_expired(mock_provider):
    rm = RiskManager(mock_provider)

    # Override fetch time to make it look expired
    rm._last_account_data = AccountSummary(100, 100)
    rm._last_fetch_time = 0

    data = await rm._get_account_data()
    assert mock_provider.call_count == 1

@pytest.mark.asyncio
async def test_validate_trade_fetch_error():
    mock_prov = AsyncMock(side_effect=Exception("API Error"))
    rm = RiskManager(mock_prov)
    check = await rm.validate_trade('AAPL', 10, 100, 'BUY', stop_loss=98)
    assert check.passed is False
    assert "Could not fetch account data" in check.reason

@pytest.mark.asyncio
async def test_validate_trade_dict_provider():
    mock_prov = AsyncMock(return_value={"NetLiquidation": 50000.0})
    rm = RiskManager(mock_prov)

    with patch('engine.risk_manager.Config') as mock_cfg:
        mock_cfg.MAX_POSITION_SIZE_PCT = 0.10
        mock_cfg.MAX_RISK_PER_TRADE_PCT = 0.02
        mock_cfg.REQUIRE_STOP_LOSS = True

        check = await rm.validate_trade('AAPL', 10, 100, 'BUY', stop_loss=98)
        assert check.passed is True

@pytest.mark.asyncio
async def test_validate_trade_negative_equity(mock_provider, mock_config):
    mock_provider.return_value = AccountSummary(-100.0, 0)
    rm = RiskManager(mock_provider)

    check = await rm.validate_trade('AAPL', 10, 100, 'BUY', stop_loss=98)
    assert check.passed is False
    assert "Account value is zero or negative" in check.reason

@pytest.mark.asyncio
async def test_risk_manager_caching_double_check():
    mock_prov = AsyncMock(return_value=AccountSummary(100, 100))
    rm = RiskManager(mock_prov)

    # We want to simulate the lock being acquired after some delay, during which another thread updated the cache
    import asyncio

    async def simulate_fetch():
        return await rm._get_account_data()

    # Pre-acquire the lock to simulate concurrency
    await rm._lock.acquire()

    task = asyncio.create_task(simulate_fetch())

    # Give it a moment to hit the lock await
    await asyncio.sleep(0.01)

    # "Another thread" updates the cache
    rm._last_account_data = AccountSummary(500, 500)
    import time
    rm._last_fetch_time = time.time()

    # Release lock so task can proceed
    rm._lock.release()

    res = await task

    # Verify double check worked and mock_prov wasn't called
    assert mock_prov.call_count == 0
    assert res.net_liquidation == 500
