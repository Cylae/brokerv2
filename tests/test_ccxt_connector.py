import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from engine.ccxt_connector import CCXTConnector
from engine.models import TradeResult

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
