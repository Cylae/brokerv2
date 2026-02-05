import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from main import analyze_symbol

@pytest.mark.asyncio
async def test_analyze_symbol_flow():
    # Setup Mocks
    mock_engine = MagicMock()
    mock_engine.get_market_data = AsyncMock(return_value={'symbol': 'AAPL', 'last': 150})
    mock_engine.execute_order = AsyncMock(return_value=MagicMock())

    mock_risk_manager = MagicMock()
    mock_risk_manager.validate_trade = AsyncMock(return_value=(True, "OK"))

    mock_ai = MagicMock()
    mock_ai.analyze_and_decide = AsyncMock(return_value={
        'decision': 'buy_stock',
        'args': {'symbol': 'AAPL', 'quantity': 10, 'stop_loss': 140, 'reason': 'Test'}
    })

    mock_db = MagicMock()
    mock_notifier = MagicMock()

    # Run Single Symbol Analysis
    await analyze_symbol(mock_engine, mock_risk_manager, mock_ai, mock_db, mock_notifier, 'AAPL')

    # Assertions
    mock_engine.get_market_data.assert_called_once_with('AAPL')
    mock_ai.analyze_and_decide.assert_awaited_once()
    mock_risk_manager.validate_trade.assert_awaited_once()
    mock_engine.execute_order.assert_awaited_once()
    mock_db.log_trade.assert_called_once()
    mock_notifier.send_trade_alert.assert_called_once()
