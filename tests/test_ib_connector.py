import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from engine.ib_connector import IBKRConnector
from ib_insync import Contract, Ticker
import eventkit

@pytest.mark.asyncio
async def test_get_market_data_success():
    """Test that get_market_data returns updated ticker when data arrives."""
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.isConnected.return_value = True
    connector.ib.qualifyContractsAsync = AsyncMock()
    connector.ib.reqHistoricalDataAsync = AsyncMock(return_value=[])

    # Mock pendingTickersEvent
    connector.ib.pendingTickersEvent = eventkit.Event()

    # Mock reqMktData to return a ticker that is initially empty
    contract = Contract(symbol='AAPL', secType='STK', exchange='SMART', currency='USD')
    ticker = Ticker(contract=contract)
    # Simulate empty/falsy values
    ticker.last = 0.0
    ticker.bid = 0.0
    ticker.ask = 0.0

    connector.ib.reqMktData.return_value = ticker

    # We need to simulate the event firing after a short delay
    async def simulate_update():
        await asyncio.sleep(0.1)
        ticker.last = 150.0
        connector.ib.pendingTickersEvent.emit({ticker})

    asyncio.create_task(simulate_update())

    start = time.time()
    data = await connector.get_market_data('AAPL')
    duration = time.time() - start

    assert data is not None
    assert data.last == 150.0

    # It should not take the full 1s timeout
    assert duration < 0.5

@pytest.mark.asyncio
async def test_get_market_data_timeout():
    """Test that get_market_data returns even if no data arrives (timeout)."""
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.isConnected.return_value = True
    connector.ib.qualifyContractsAsync = AsyncMock()
    connector.ib.reqHistoricalDataAsync = AsyncMock(return_value=[])

    # Mock pendingTickersEvent
    connector.ib.pendingTickersEvent = eventkit.Event()

    ticker = Ticker(contract=Contract(symbol='AAPL'))
    ticker.last = 0.0
    ticker.bid = 0.0
    ticker.ask = 0.0
    connector.ib.reqMktData.return_value = ticker

    start = time.time()
    # This should wait for about 1 second
    data = await connector.get_market_data('AAPL')
    duration = time.time() - start

    # Should be close to 1.0s (polling 20*0.05=1.0)
    assert duration >= 0.95

@pytest.mark.asyncio
async def test_ib_connect_success():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.isConnected.return_value = False
    connector.ib.connectAsync = AsyncMock()

    await connector.connect()

    connector.ib.connectAsync.assert_called_once_with('127.0.0.1', 7497, 1)
    assert connector.connected is True

@pytest.mark.asyncio
async def test_ib_connect_already_connected():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.isConnected.return_value = True
    connector.ib.connectAsync = AsyncMock()

    await connector.connect()

    connector.ib.connectAsync.assert_not_called()
    assert connector.connected is True

@pytest.mark.asyncio
async def test_ib_connect_failure():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.isConnected.return_value = False
    connector.ib.connectAsync.side_effect = Exception("Connection failed")

    with pytest.raises(Exception, match="Connection failed"):
        await connector.connect()

    assert connector.connected is False

@pytest.mark.asyncio
async def test_ib_disconnect():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.isConnected.return_value = True
    connector.connected = True

    await connector.disconnect()

    connector.ib.disconnect.assert_called_once()
    assert connector.connected is False

@pytest.mark.asyncio
async def test_ib_check_connection():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.isConnected.side_effect = [True, False]

    assert await connector.check_connection() is True
    assert await connector.check_connection() is False

@pytest.mark.asyncio
async def test_ib_get_market_data_cache_hit():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()

    # Mock snapshot to return instantly
    connector.ib.pendingTickersEvent = eventkit.Event()
    contract = Contract(symbol='AAPL', secType='STK', exchange='SMART', currency='USD')
    ticker = Ticker(contract=contract)
    ticker.last = 150.0
    connector.ib.reqMktData.return_value = ticker

    # Pre-populate cache
    current_time = asyncio.get_event_loop().time()
    connector._historical_cache['AAPL'] = {
        'time': current_time,
        'technicals': {'SMA_20': 140.0}
    }

    with patch('engine.ib_connector.asyncio.get_event_loop') as mock_loop:
        mock_loop_instance = MagicMock()
        mock_loop_instance.time.return_value = current_time + 10
        mock_loop.return_value = mock_loop_instance

        data = await connector.get_market_data('AAPL')
        assert data.indicators == {'SMA_20': 140.0}

        # Historical data should NOT be requested if cache hits
        assert connector.ib.reqHistoricalDataAsync.call_count == 0

@pytest.mark.asyncio
async def test_ib_get_market_data_qualify_error():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync.side_effect = Exception("Qualify failed")

    data = await connector.get_market_data("AAPL")
    assert data is None

@pytest.mark.asyncio
async def test_ib_get_market_data_no_data():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()
    connector.ib.reqHistoricalDataAsync = AsyncMock(return_value=[])

    # Mock Event
    connector.ib.pendingTickersEvent = eventkit.Event()

    ticker = Ticker(contract=Contract(symbol='AAPL'))
    ticker.last = 0.0
    ticker.close = 0.0
    connector.ib.reqMktData.return_value = ticker

    data = await connector.get_market_data("AAPL")
    assert data is None

@pytest.mark.asyncio
async def test_ib_execute_order_market_buy():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()

    trade_mock = MagicMock()
    trade_mock.order.orderId = 123
    trade_mock.orderStatus.status = "Submitted"
    connector.ib.placeOrder.return_value = trade_mock

    res = await connector.execute_order("AAPL", "BUY", 10)

    assert res.order_id == "123"
    assert res.status == "Submitted"
    connector.ib.placeOrder.assert_called_once()

    args, kwargs = connector.ib.placeOrder.call_args
    order = args[1]
    assert order.action == "BUY"
    assert order.totalQuantity == 10
    assert order.orderType == "MKT"

@pytest.mark.asyncio
async def test_ib_execute_order_limit_missing_price():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()

    with pytest.raises(ValueError, match="Price needed for LMT"):
        await connector.execute_order("AAPL", "BUY", 10, order_type="LMT")

@pytest.mark.asyncio
async def test_ib_execute_order_unknown_type():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()

    with pytest.raises(ValueError, match="Unknown Order Type: INVALID"):
        await connector.execute_order("AAPL", "BUY", 10, order_type="INVALID")

@pytest.mark.asyncio
async def test_ib_execute_order_with_brackets():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()

    parent_trade = MagicMock()
    parent_trade.order.orderId = 123
    parent_trade.orderStatus.status = "Submitted"

    stop_trade = MagicMock()
    limit_trade = MagicMock()

    connector.ib.placeOrder.side_effect = [parent_trade, stop_trade, limit_trade]

    stop_order = MagicMock()
    limit_order = MagicMock()
    connector.ib.bracketStopOrder.return_value = stop_order
    connector.ib.bracketLimitOrder.return_value = limit_order

    res = await connector.execute_order("AAPL", "BUY", 10, stop_loss=140.0, take_profit=160.0)

    assert res.order_id == "123"
    assert connector.ib.placeOrder.call_count == 3
    connector.ib.bracketStopOrder.assert_called_once()
    connector.ib.bracketLimitOrder.assert_called_once()

@pytest.mark.asyncio
async def test_ib_get_account_summary():
    connector = IBKRConnector()
    connector.ib = MagicMock()

    class MockItem:
        def __init__(self, tag, value):
            self.tag = tag
            self.value = value

    connector.ib.accountSummaryAsync = AsyncMock(return_value=[
        MockItem("NetLiquidation", "10000.50"),
        MockItem("TotalCashValue", "5000.25"),
        MockItem("OtherTag", "123")
    ])

    summary = await connector.get_account_summary()

    assert summary.net_liquidation == 10000.50
    assert summary.total_cash == 5000.25
    assert summary.currency == "USD"

@pytest.mark.asyncio
async def test_ib_get_positions():
    connector = IBKRConnector()
    connector.ib = MagicMock()

    class MockPosition:
        def __init__(self, symbol, pos, avg_cost):
            self.contract = MagicMock()
            self.contract.symbol = symbol
            self.position = pos
            self.avgCost = avg_cost

    connector.ib.positions.return_value = [
        MockPosition("AAPL", 10, 150.0),
        MockPosition("TSLA", 5, 200.0)
    ]

    positions = await connector.get_positions()

    assert len(positions) == 2
    assert positions[0].symbol == "AAPL"
    assert positions[0].quantity == 10
    assert positions[0].avg_cost == 150.0
    assert positions[1].symbol == "TSLA"


@pytest.mark.asyncio
async def test_ib_get_market_data_with_bars():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()

    # Mock Event
    connector.ib.pendingTickersEvent = eventkit.Event()

    ticker = Ticker(contract=Contract(symbol='AAPL'))
    ticker.last = 150.0
    connector.ib.reqMktData.return_value = ticker

    # Return some mock data for history
    class MockBar:
        def __init__(self, date, open, high, low, close, volume):
            self.date = date
            self.open = open
            self.high = high
            self.low = low
            self.close = close
            self.volume = volume

    mock_bars = [MockBar("2023-01-01", 100, 110, 90, 105, 1000)]
    connector.ib.reqHistoricalDataAsync = AsyncMock(return_value=mock_bars)

    with patch('engine.ib_connector.util.df') as mock_df, \
         patch('engine.ib_connector.Indicators.get_technical_summary') as mock_inds:
        mock_inds.return_value = {'SMA_20': 100.0}

        data = await connector.get_market_data("AAPL")

        assert data is not None
        assert data.indicators == {'SMA_20': 100.0}

@pytest.mark.asyncio
async def test_ib_execute_order_limit():
    connector = IBKRConnector()
    connector.ib = MagicMock()
    connector.ib.qualifyContractsAsync = AsyncMock()

    trade_mock = MagicMock()
    trade_mock.order.orderId = 123
    trade_mock.orderStatus.status = "Submitted"
    connector.ib.placeOrder.return_value = trade_mock

    res = await connector.execute_order("AAPL", "BUY", 10, order_type="LMT", price=150.0)

    assert res.order_id == "123"
    args, kwargs = connector.ib.placeOrder.call_args
    order = args[1]
    assert order.action == "BUY"
    assert order.totalQuantity == 10
    assert order.orderType == "LMT"
    assert order.lmtPrice == 150.0
