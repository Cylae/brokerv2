import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from main import run_trading_cycle

@pytest.mark.asyncio
async def test_run_trading_cycle_hallucination_mismatch():
    # Setup Mocks
    mock_engine = MagicMock()
    mock_engine.get_market_data = AsyncMock(return_value={'symbol': 'AAPL', 'last': 150})
    mock_engine.execute_order = AsyncMock()

    mock_risk_manager = MagicMock()
    mock_db = MagicMock()
    mock_notifier = MagicMock()

    mock_ai = MagicMock()
    # AI returns decision for TSLA when we asked for AAPL
    mock_ai.analyze_and_decide.return_value = {
        'decision': 'buy_stock',
        'args': {'symbol': 'TSLA', 'quantity': 10, 'reason': 'I like TSLA'}
    }

    # Mock Market Open
    with patch('engine.market_utils.MarketSchedule.is_market_open', return_value=True):
        symbols = ['AAPL']

        # Run
        await run_trading_cycle(mock_engine, mock_risk_manager, mock_ai, mock_db, mock_notifier, symbols)

    # Assert execute_order was NOT called because of mismatch
    mock_engine.execute_order.assert_not_called()

@pytest.mark.asyncio
async def test_run_trading_cycle_correct_match():
    # Setup Mocks
    mock_engine = MagicMock()
    mock_engine.get_market_data = AsyncMock(return_value={'symbol': 'AAPL', 'last': 150})
    mock_trade = MagicMock()
    mock_trade.order.orderId = 123
    mock_engine.execute_order = AsyncMock(return_value=mock_trade)

    mock_risk_manager = MagicMock()
    mock_risk_manager.validate_trade = AsyncMock(return_value=(True, "OK"))

    mock_db = MagicMock()
    mock_notifier = MagicMock()

    mock_ai = MagicMock()
    # AI returns decision for AAPL
    mock_ai.analyze_and_decide.return_value = {
        'decision': 'buy_stock',
        'args': {'symbol': 'AAPL', 'quantity': 10, 'stop_loss': 145, 'reason': 'I like AAPL'}
    }

    # Mock Market Open
    with patch('engine.market_utils.MarketSchedule.is_market_open', return_value=True):
        symbols = ['AAPL']

        # Run
        await run_trading_cycle(mock_engine, mock_risk_manager, mock_ai, mock_db, mock_notifier, symbols)

    # Assert execute_order WAS called
    mock_engine.execute_order.assert_called_once()

    # Assert DB logging was called
    mock_db.log_trade.assert_called_once()

    # Assert Notification was sent
    mock_notifier.send_trade_alert.assert_called_once()

@pytest.mark.asyncio
async def test_run_trading_cycle_market_closed():
    mock_engine = MagicMock()
    mock_risk_manager = MagicMock()
    mock_ai = MagicMock()
    mock_db = MagicMock()
    mock_notifier = MagicMock()

    with patch('engine.market_utils.MarketSchedule.is_market_open', return_value=False):
        await run_trading_cycle(mock_engine, mock_risk_manager, mock_ai, mock_db, mock_notifier, ['AAPL'])

    mock_engine.get_market_data.assert_not_called()
