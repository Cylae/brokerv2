import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from engine.ccxt_connector import CCXTConnector

@pytest.fixture
def mock_ccxt_exchange():
    exchange = MagicMock()
    exchange.load_markets = AsyncMock()
    exchange.close = AsyncMock()
    exchange.fetch_ticker = AsyncMock(return_value={
        'last': 50000.0,
        'bid': 49990.0,
        'ask': 50010.0,
        'baseVolume': 100.0,
        'close': 50000.0
    })
    exchange.fetch_ohlcv = AsyncMock(return_value=[])
    exchange.create_order = AsyncMock(return_value={'id': '12345', 'status': 'closed', 'price': 50000.0})
    exchange.fetch_balance = AsyncMock(return_value={'total': {'USDT': 1000.0, 'BTC': 0.5}})
    return exchange

@pytest.mark.asyncio
async def test_ccxt_connect(mock_ccxt_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_ccxt_exchange):
        connector = CCXTConnector('key', 'secret', exchange_id='binance')
        await connector.connect()
        mock_ccxt_exchange.load_markets.assert_called_once()
        assert connector.connected is True

@pytest.mark.asyncio
async def test_ccxt_get_data_unified(mock_ccxt_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_ccxt_exchange):
        connector = CCXTConnector('key', 'secret', 'binance')
        data = await connector.get_market_data('BTC/USDT')

        assert data.symbol == 'BTC/USDT'
        assert data.last == 50000.0
        assert isinstance(data.indicators, dict)

@pytest.mark.asyncio
async def test_ccxt_execute_order_unified(mock_ccxt_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_ccxt_exchange):
        connector = CCXTConnector('key', 'secret', 'binance')
        res = await connector.execute_order('BTC/USDT', 'BUY', 0.1)

        assert res.order_id == '12345'
        assert res.symbol == 'BTC/USDT'
        assert res.action == 'BUY'

@pytest.mark.asyncio
async def test_ccxt_get_positions_unified(mock_ccxt_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_ccxt_exchange):
        connector = CCXTConnector('key', 'secret', 'binance')
        positions = await connector.get_positions()

        assert len(positions) == 1
        assert positions[0].symbol == 'BTC'
        assert positions[0].quantity == 0.5
