import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_connector_connect(mock_ib_connector, mock_ib):
    mock_ib.isConnected.return_value = False
    await mock_ib_connector.connect()

    mock_ib.connectAsync.assert_called_once()
    assert mock_ib_connector.connected is True

@pytest.mark.asyncio
async def test_trading_engine_get_market_data(mock_ib_connector, mock_ib):
    from engine.trading_engine import TradingEngine
    engine = TradingEngine(mock_ib_connector)

    # Mock ticker
    ticker = MagicMock()
    ticker.last = 150.0
    ticker.bid = 149.9
    ticker.ask = 150.1
    ticker.volume = 1000
    ticker.close = 149.0

    mock_ib.reqMktData.return_value = ticker
    mock_ib.reqHistoricalDataAsync = AsyncMock(return_value=[])

    data = await engine.get_market_data('AAPL')

    assert data is not None
    assert data['symbol'] == 'AAPL'

@pytest.mark.asyncio
async def test_trading_engine_execute_order_simple(mock_ib_connector, mock_ib):
    from engine.trading_engine import TradingEngine
    engine = TradingEngine(mock_ib_connector)

    await engine.execute_order('AAPL', 'BUY', 10, 'MKT')

    mock_ib.placeOrder.assert_called_once()

@pytest.mark.asyncio
async def test_trading_engine_execute_bracket_order(mock_ib_connector, mock_ib):
    from engine.trading_engine import TradingEngine
    engine = TradingEngine(mock_ib_connector)

    # Mock bracket helpers
    mock_ib.bracketStopOrder = MagicMock(return_value=MagicMock())
    mock_ib.bracketLimitOrder = MagicMock(return_value=MagicMock())

    await engine.execute_order('AAPL', 'BUY', 10, 'MKT', stop_loss=140, take_profit=160)

    # Should place 3 orders (Parent, SL, TP)
    assert mock_ib.placeOrder.call_count == 3
    mock_ib.bracketStopOrder.assert_called_once()
    mock_ib.bracketLimitOrder.assert_called_once()
