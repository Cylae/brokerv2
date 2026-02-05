import pytest
from unittest.mock import MagicMock, AsyncMock
from main import run_trading_cycle

@pytest.mark.asyncio
async def test_run_trading_cycle_hallucination_mismatch():
    # Setup Mocks
    mock_engine = MagicMock()
    mock_engine.get_market_data = AsyncMock(return_value={'symbol': 'AAPL', 'last': 150})
    mock_engine.execute_order = AsyncMock()

    mock_risk_manager = MagicMock()

    mock_ai = MagicMock()
    # AI returns decision for TSLA when we asked for AAPL
    mock_ai.analyze_and_decide.return_value = {
        'decision': 'buy_stock',
        'args': {'symbol': 'TSLA', 'quantity': 10, 'reason': 'I like TSLA'}
    }

    symbols = ['AAPL']

    # Run
    await run_trading_cycle(mock_engine, mock_risk_manager, mock_ai, symbols)

    # Assert execute_order was NOT called because of mismatch
    mock_engine.execute_order.assert_not_called()

@pytest.mark.asyncio
async def test_run_trading_cycle_correct_match():
    # Setup Mocks
    mock_engine = MagicMock()
    mock_engine.get_market_data = AsyncMock(return_value={'symbol': 'AAPL', 'last': 150})
    mock_engine.execute_order = AsyncMock()

    mock_risk_manager = MagicMock()
    # Risk Manager MUST approve the trade
    mock_risk_manager.validate_trade = AsyncMock(return_value=(True, "OK"))

    mock_ai = MagicMock()
    # AI returns decision for AAPL
    mock_ai.analyze_and_decide.return_value = {
        'decision': 'buy_stock',
        'args': {'symbol': 'AAPL', 'quantity': 10, 'stop_loss': 145, 'reason': 'I like AAPL'}
    }

    symbols = ['AAPL']

    # Run
    await run_trading_cycle(mock_engine, mock_risk_manager, mock_ai, symbols)

    # Assert execute_order WAS called
    mock_engine.execute_order.assert_called_once()
