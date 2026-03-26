import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from engine.ccxt_connector import CCXTConnector
from engine.models import TradeResult

@pytest.mark.asyncio
async def test_ccxt_init_unsupported_exchange():
    with pytest.raises(ValueError, match="Exchange 'unsupported' not supported"):
        CCXTConnector("key", "secret", exchange_id="unsupported")

@pytest.mark.asyncio
async def test_ccxt_init_supported_exchange():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange_cls = MagicMock()
        mock_ccxt.binance = mock_exchange_cls

        connector = CCXTConnector("key", "secret", exchange_id="binance", testnet=True, passphrase="pwd")

        assert connector.api_key == "key"
        assert connector.secret_key == "secret"
        assert connector.passphrase == "pwd"
        assert connector.exchange_id == "binance"
        assert connector.testnet == True
        mock_exchange_cls.assert_called_once_with({
            'apiKey': 'key',
            'secret': 'secret',
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
            'password': 'pwd'
        })
        mock_exchange_cls.return_value.set_sandbox_mode.assert_called_once_with(True)

@pytest.mark.asyncio
async def test_ccxt_connect_success():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        await connector.connect()

        mock_exchange.load_markets.assert_called_once()
        assert connector.connected is True

@pytest.mark.asyncio
async def test_ccxt_connect_failure():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.load_markets.side_effect = Exception("Load markets failed")
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        with pytest.raises(Exception, match="Load markets failed"):
            await connector.connect()

        assert connector.connected is False

@pytest.mark.asyncio
async def test_ccxt_disconnect():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        connector.connected = True
        await connector.disconnect()

        mock_exchange.close.assert_called_once()
        assert connector.connected is False

@pytest.mark.asyncio
async def test_ccxt_check_connection():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        connector.connected = True
        assert await connector.check_connection() is True
        connector.connected = False
        assert await connector.check_connection() is False

@pytest.mark.asyncio
async def test_ccxt_get_market_data_success():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.return_value = {
            'last': 50000.0,
            'bid': 49990.0,
            'ask': 50010.0,
            'baseVolume': 100.0
        }
        # mock ohlcv
        mock_exchange.fetch_ohlcv.return_value = [
            [1678886400000, 1.0, 2.0, 0.5, 1.5, 1000]
        ]
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")

        with patch('engine.ccxt_connector.Indicators.get_technical_summary', return_value={'SMA_20': 45000.0}) as mock_inds:
            data = await connector.get_market_data("BTC/USDT")

            assert data is not None
            assert data.symbol == "BTC/USDT"
            assert data.last == 50000.0
            assert data.bid == 49990.0
            assert data.ask == 50010.0
            assert data.volume == 100.0
            assert data.indicators == {'SMA_20': 45000.0}
            mock_exchange.fetch_ticker.assert_called_once_with("BTC/USDT")
            mock_exchange.fetch_ohlcv.assert_called_once_with("BTC/USDT", '1h', limit=100)

@pytest.mark.asyncio
async def test_ccxt_get_market_data_symbol_standardization():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.return_value = {
            'last': 50000.0, 'bid': 49990.0, 'ask': 50010.0, 'baseVolume': 100.0
        }
        mock_exchange.fetch_ohlcv.return_value = []
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")

        data = await connector.get_market_data("BTC")

        assert data.symbol == "BTC/USDT"
        mock_exchange.fetch_ticker.assert_called_once_with("BTC/USDT")

@pytest.mark.asyncio
async def test_ccxt_get_market_data_fetch_error():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.side_effect = Exception("API error")
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        data = await connector.get_market_data("BTC/USDT")

        assert data is None

@pytest.mark.asyncio
async def test_ccxt_execute_order_market_buy_no_stop_loss():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.create_order.return_value = {
            'id': '123', 'status': 'closed', 'price': 50000.0
        }
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        res = await connector.execute_order("BTC/USDT", "BUY", 1.0)

        assert res.order_id == "123"
        assert res.symbol == "BTC/USDT"
        assert res.action == "BUY"
        assert res.quantity == 1.0
        assert res.price == 50000.0
        assert res.status == "CLOSED"
        assert res.asset_type == "CRYPTO"
        mock_exchange.create_order.assert_called_once_with("BTC/USDT", "market", "buy", 1.0, params={})

@pytest.mark.asyncio
async def test_ccxt_execute_order_limit_missing_price():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        with pytest.raises(ValueError, match="Price needed for Limit"):
            await connector.execute_order("BTC/USDT", "BUY", 1.0, order_type="LMT")

@pytest.mark.asyncio
async def test_ccxt_execute_order_limit_with_price():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.create_order.return_value = {
            'id': '123', 'status': 'open', 'price': 49000.0
        }
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        res = await connector.execute_order("BTC/USDT", "BUY", 1.0, order_type="LMT", price=49000.0)

        assert res.order_id == "123"
        assert res.price == 49000.0
        mock_exchange.create_order.assert_called_once_with("BTC/USDT", "limit", "buy", 1.0, 49000.0, {})

@pytest.mark.asyncio
async def test_binance_stop_loss():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange_cls = MagicMock()
        mock_exchange = AsyncMock()
        mock_exchange_cls.return_value = mock_exchange
        mock_ccxt.binance = mock_exchange_cls

        connector = CCXTConnector("key", "secret", exchange_id="binance")

        # Mock create_order sequence
        mock_exchange.create_order.side_effect = [
            {'id': '123', 'status': 'closed', 'price': 100.0}, # Parent
            {'id': '124', 'status': 'open'} # Stop Loss
        ]

        await connector.execute_order("BTC/USDT", "BUY", 1.0, stop_loss=90.0)

        assert mock_exchange.create_order.call_count == 2

        # Verify Stop Loss call
        args, kwargs = mock_exchange.create_order.call_args_list[1]
        # args: symbol, type, side, quantity, price, params
        assert args[1] == 'STOP_LOSS_LIMIT'
        assert args[2] == 'sell'
        assert args[4] == 90.0

@pytest.mark.asyncio
async def test_generic_stop_loss():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange_cls = MagicMock()
        mock_exchange = AsyncMock()
        mock_exchange_cls.return_value = mock_exchange
        mock_ccxt.coinbase = mock_exchange_cls

        connector = CCXTConnector("key", "secret", exchange_id="coinbase")

        # Mock create_order sequence
        mock_exchange.create_order.side_effect = [
            {'id': 'abc', 'status': 'closed', 'price': 50.0}, # Parent
            {'id': 'xyz', 'status': 'open'} # Stop Loss
        ]

        await connector.execute_order("ETH/USDT", "BUY", 1.0, stop_loss=45.0)

        # Verify Stop Loss call
        # args: symbol, type, side, quantity, price, params
        args, kwargs = mock_exchange.create_order.call_args_list[1]
        assert args[1] == 'stop_market'
        assert args[4] is None

@pytest.mark.asyncio
async def test_generic_stop_loss_fallback_to_stop_limit():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_ccxt.kraken = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="kraken")

        def create_order_side_effect(*args, **kwargs):
            # args: symbol, type, side, quantity, price, params
            if args[1] == 'market':
                return {'id': 'parent', 'status': 'closed', 'price': 100.0}
            elif args[1] == 'stop_market':
                raise Exception("Stop market not supported")
            elif args[1] == 'stop_limit':
                return {'id': 'stop_limit_123', 'status': 'open'}

        mock_exchange.create_order.side_effect = create_order_side_effect

        await connector.execute_order("ETH/USDT", "BUY", 1.0, stop_loss=90.0)

        assert mock_exchange.create_order.call_count == 3
        # 1: parent (market), 2: stop_market (fails), 3: stop_limit (succeeds)
        args3, _ = mock_exchange.create_order.call_args_list[2]
        assert args3[1] == 'stop_limit'
        assert args3[4] == 90.0

@pytest.mark.asyncio
async def test_stop_loss_emergency_close():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")

        def create_order_side_effect(*args, **kwargs):
            if args[1] == 'market' and args[2] == 'buy':
                return {'id': 'parent', 'status': 'closed', 'price': 100.0}
            elif args[1] == 'STOP_LOSS_LIMIT':
                raise Exception("Stop loss placement failed completely")
            elif args[1] == 'market' and args[2] == 'sell':
                return {'id': 'emergency_close', 'status': 'closed'}

        mock_exchange.create_order.side_effect = create_order_side_effect

        await connector.execute_order("BTC/USDT", "BUY", 1.0, stop_loss=90.0)

        assert mock_exchange.create_order.call_count == 3
        # 1: parent, 2: stop_loss (fails), 3: emergency close (market sell)
        args3, _ = mock_exchange.create_order.call_args_list[2]
        assert args3[1] == 'market'
        assert args3[2] == 'sell'
        assert args3[3] == 1.0

@pytest.mark.asyncio
async def test_get_account_summary_success():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_balance.return_value = {
            'total': {'USDT': 1000.0, 'BTC': 0.5}
        }
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        summary = await connector.get_account_summary()

        assert summary.net_liquidation == 1000.0
        assert summary.total_cash == 1000.0
        assert summary.currency == "USDT"

@pytest.mark.asyncio
async def test_ccxt_connector_get_market_data_cache_hit():
    from unittest.mock import MagicMock, AsyncMock, patch
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange_cls = MagicMock()
        mock_exchange = AsyncMock()

        # Mock fetch_ticker
        mock_exchange.fetch_ticker.return_value = {
            'last': 50000.0,
            'bid': 49990.0,
            'ask': 50010.0,
            'baseVolume': 100.0
        }

        mock_exchange_cls.return_value = mock_exchange
        mock_ccxt.binance = mock_exchange_cls

        connector = CCXTConnector("key", "secret", exchange_id="binance")

        import time
        current_time = time.time()
        connector._historical_cache['BTC/USDT'] = {
            'time': current_time,
            'technicals': {'SMA_20': 40000.0}
        }

        with patch('engine.ccxt_connector.asyncio.get_event_loop') as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.time.return_value = current_time + 10
            mock_loop.return_value = mock_loop_instance

            data = await connector.get_market_data("BTC/USDT")

            assert data.symbol == "BTC/USDT"
            assert data.last == 50000.0
            assert data.volume == 100.0
            assert data.indicators == {'SMA_20': 40000.0}
            assert mock_exchange.fetch_ohlcv.call_count == 0

@pytest.mark.asyncio
async def test_get_account_summary_fallback_usd():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_balance.return_value = {
            'total': {'USD': 5000.0, 'ETH': 2.0}
        }
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        summary = await connector.get_account_summary()

        assert summary.net_liquidation == 5000.0

@pytest.mark.asyncio
async def test_get_account_summary_error():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_balance.side_effect = Exception("Balance error")
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        summary = await connector.get_account_summary()

        assert summary.net_liquidation == 0.0
        assert summary.currency == "USDT"

@pytest.mark.asyncio
async def test_get_positions_success():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_balance.return_value = {
            'total': {
                'USDT': 1000.0,
                'BTC': 0.5,
                'ETH': 0.00001 # Dust, should be ignored
            }
        }
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        positions = await connector.get_positions()

        assert len(positions) == 1
        assert positions[0].symbol == "BTC/USDT"
        assert positions[0].quantity == 0.5
        assert positions[0].asset_type == "CRYPTO"

@pytest.mark.asyncio
async def test_get_positions_error():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_balance.side_effect = Exception("Positions error")
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        positions = await connector.get_positions()

        assert positions == []

@pytest.mark.asyncio
async def test_get_market_data_processing_error():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.return_value = {} # Empty dict to cause KeyError on ['last']
        mock_exchange.fetch_ohlcv.return_value = []
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        data = await connector.get_market_data("BTC/USDT")

        assert data is None

@pytest.mark.asyncio
async def test_execute_order_creation_error():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.create_order.side_effect = Exception("Order rejected")
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        with pytest.raises(Exception, match="Order rejected"):
            await connector.execute_order("BTC/USDT", "BUY", 1.0)

@pytest.mark.asyncio
async def test_stop_loss_emergency_close_failed():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")

        def create_order_side_effect(*args, **kwargs):
            if args[1] == 'market' and args[2] == 'buy':
                return {'id': 'parent', 'status': 'closed', 'price': 100.0}
            elif args[1] == 'STOP_LOSS_LIMIT':
                raise Exception("Stop loss placement failed completely")
            elif args[1] == 'market' and args[2] == 'sell':
                raise Exception("Emergency close failed")

        mock_exchange.create_order.side_effect = create_order_side_effect

        # Shouldn't raise, just logs critical error
        await connector.execute_order("BTC/USDT", "BUY", 1.0, stop_loss=90.0)

        assert mock_exchange.create_order.call_count == 3

@pytest.mark.asyncio
async def test_execute_order_symbol_standardization():
    with patch('engine.ccxt_connector.ccxt') as mock_ccxt:
        mock_exchange = AsyncMock()
        mock_exchange.create_order.return_value = {
            'id': '123', 'status': 'closed', 'price': 50000.0
        }
        mock_ccxt.binance = MagicMock(return_value=mock_exchange)

        connector = CCXTConnector("key", "secret", exchange_id="binance")
        res = await connector.execute_order("BTC", "BUY", 1.0)

        assert res.symbol == "BTC/USDT"
        mock_exchange.create_order.assert_called_once_with("BTC/USDT", "market", "buy", 1.0, params={})
