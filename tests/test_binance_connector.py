import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from engine.binance_connector import BinanceConnector

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
    exchange.create_order = AsyncMock(return_value={'id': '12345'})
    exchange.fetch_balance = AsyncMock(return_value={'total': {'USDT': 1000.0}})
    return exchange

@pytest.mark.asyncio
async def test_binance_connect(mock_ccxt_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_ccxt_exchange):
        connector = BinanceConnector('key', 'secret')
        await connector.connect()
        mock_ccxt_exchange.load_markets.assert_called_once()
        assert connector.connected is True

@pytest.mark.asyncio
async def test_binance_execute_order_with_sl(mock_ccxt_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_ccxt_exchange):
        connector = BinanceConnector('key', 'secret')

        # Test Buy with Stop Loss
        res = await connector.execute_order('BTC/USDT', 'BUY', 0.1, stop_loss=45000)

        # Expect 2 calls: 1 Entry, 1 Stop Loss
        assert mock_ccxt_exchange.create_order.call_count == 2

        # Check Entry
        args_entry, _ = mock_ccxt_exchange.create_order.call_args_list[0]
        assert args_entry[0] == 'BTC/USDT'
        assert args_entry[1] == 'market'
        assert args_entry[2] == 'buy'

        # Check Stop Loss
        args_sl, _ = mock_ccxt_exchange.create_order.call_args_list[1]
        assert args_sl[0] == 'BTC/USDT'
        assert args_sl[1] == 'STOP_LOSS_LIMIT'
        assert args_sl[2] == 'sell'
        assert args_sl[4] == 45000 # Limit Price

@pytest.mark.asyncio
async def test_binance_sl_failure_emergency_close(mock_ccxt_exchange):
    with patch('ccxt.async_support.binance', return_value=mock_ccxt_exchange):
        connector = BinanceConnector('key', 'secret')

        # Make Stop Loss fail
        mock_ccxt_exchange.create_order.side_effect = [
            {'id': '123'}, # Entry succeeds
            Exception("SL Failed"), # SL Fails
            {'id': '999'} # Emergency Close succeeds
        ]

        res = await connector.execute_order('BTC/USDT', 'BUY', 0.1, stop_loss=45000)

        # Expect 3 calls: Entry, SL (fail), Emergency Close
        assert mock_ccxt_exchange.create_order.call_count == 3

        # Check Emergency Close
        args_close, _ = mock_ccxt_exchange.create_order.call_args_list[2]
        assert args_close[1] == 'market'
        assert args_close[2] == 'sell'
