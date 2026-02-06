import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from engine.ccxt_connector import CCXTConnector

@pytest.fixture
def mock_exchange():
    exchange = MagicMock()
    exchange.load_markets = AsyncMock()
    exchange.close = AsyncMock()
    exchange.fetch_ticker = AsyncMock(return_value={
        'last': 50000.0, 'bid': 49990.0, 'ask': 50010.0, 'baseVolume': 100.0, 'close': 50000.0
    })
    exchange.fetch_ohlcv = AsyncMock(return_value=[])
    exchange.create_order = AsyncMock(return_value={'id': '123', 'status': 'closed', 'price': 50000.0})
    exchange.fetch_balance = AsyncMock(return_value={'total': {'USDT': 1000.0}})
    return exchange

@pytest.mark.asyncio
async def test_coinbase_stop_loss(mock_exchange):
    with patch('ccxt.async_support.coinbase', return_value=mock_exchange):
        connector = CCXTConnector('key', 'secret', exchange_id='coinbase')
        await connector.connect()

        # Test Buy with Stop Loss
        await connector.execute_order('BTC/USD', 'BUY', 0.1, stop_loss=40000.0)

        # Verify calls
        # 1. Market Buy
        # 2. Stop Loss (Coinbase specific)
        calls = mock_exchange.create_order.call_args_list
        assert len(calls) == 2

        stop_call = calls[1]
        args, _ = stop_call

        # create_order(symbol, type, side, amount, price, params)
        assert args[0] == 'BTC/USD' # Symbol
        assert args[1] == 'market'  # Type
        assert args[2] == 'sell'    # Side
        assert args[3] == 0.1       # Quantity
        # args[4] is price (None for market)
        assert args[5]['stop'] == 'loss'
        assert args[5]['stopPrice'] == 40000.0

@pytest.mark.asyncio
async def test_kraken_stop_loss(mock_exchange):
    with patch('ccxt.async_support.kraken', return_value=mock_exchange):
        connector = CCXTConnector('key', 'secret', exchange_id='kraken')
        await connector.connect()

        await connector.execute_order('BTC/USD', 'BUY', 0.1, stop_loss=40000.0)

        calls = mock_exchange.create_order.call_args_list
        stop_call = calls[1]
        args, _ = stop_call

        # Expected for Kraken: type='stop-loss', price=40000.0
        assert args[1] == 'stop-loss'
        assert args[4] == 40000.0

@pytest.mark.asyncio
async def test_symbol_standardization(mock_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_exchange):
        connector = CCXTConnector('key', 'secret', exchange_id='binance')

        # Case 1: No slash -> Add USDT
        await connector.get_market_data('BTC')
        mock_exchange.fetch_ticker.assert_called_with('BTC/USDT')

        # Case 2: Slash exists -> Keep as is
        await connector.get_market_data('ETH/BTC')
        mock_exchange.fetch_ticker.assert_called_with('ETH/BTC')
