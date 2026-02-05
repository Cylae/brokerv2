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

    # Mock Historical Data (return empty list or None for simplicity in basic test)
    # The code expects `bars` to be truthy to compute indicators.
    mock_ib.reqHistoricalDataAsync = AsyncMock(return_value=[])

    data = await engine.get_market_data('AAPL')

    assert data is not None
    assert data['symbol'] == 'AAPL'
    assert data['last'] == 150.0
    mock_ib.qualifyContractsAsync.assert_called_once()
    mock_ib.reqMktData.assert_called_once()
    mock_ib.reqHistoricalDataAsync.assert_called_once()

@pytest.mark.asyncio
async def test_trading_engine_execute_order(mock_ib_connector, mock_ib):
    from engine.trading_engine import TradingEngine
    engine = TradingEngine(mock_ib_connector)

    await engine.execute_order('AAPL', 'BUY', 10, 'MKT')

    mock_ib.placeOrder.assert_called_once()
    args, _ = mock_ib.placeOrder.call_args
    contract, order = args

    assert contract.symbol == 'AAPL'
    assert order.action == 'BUY'
    assert order.totalQuantity == 10
    assert order.orderType == 'MKT'
