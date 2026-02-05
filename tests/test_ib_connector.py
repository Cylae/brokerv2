import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock
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
