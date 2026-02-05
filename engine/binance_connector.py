import ccxt.async_support as ccxt
import logging
import asyncio
import pandas as pd
from datetime import datetime
from .base_connector import BaseConnector
from .indicators import Indicators

class BinanceConnector(BaseConnector):
    def __init__(self, api_key, secret_key, testnet=False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        if testnet:
            self.exchange.set_sandbox_mode(True)

        self.logger = logging.getLogger(__name__)
        self.connected = False

    async def connect(self):
        try:
            await self.exchange.load_markets()
            self.connected = True
            self.logger.info("Connected to Binance.")
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        await self.exchange.close()
        self.connected = False
        self.logger.info("Disconnected from Binance.")

    async def check_connection(self):
        return self.connected

    async def get_market_data(self, symbol):
        if '/' not in symbol:
            if len(symbol) <= 5:
                symbol = f"{symbol}/USDT"

        try:
            # OPTIMIZATION: Fetch Ticker and OHLCV concurrently
            ticker_task = self.exchange.fetch_ticker(symbol)
            bars_task = self.exchange.fetch_ohlcv(symbol, '1h', limit=100) # Reduced limit from 240 to 100 for speed (sufficient for SMA50/RSI/BB)

            ticker, bars = await asyncio.gather(ticker_task, bars_task)

            snapshot = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'close': ticker['close']
            }

            if bars:
                df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                technicals = Indicators.get_technical_summary(df)
            else:
                technicals = {}

            return {**snapshot, **technicals}

        except Exception as e:
            self.logger.error(f"Error fetching Binance data for {symbol}: {e}")
            return None

    async def execute_order(self, symbol, action, quantity, order_type='MKT', price=None, stop_loss=None, take_profit=None):
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"

        side = action.lower()
        type_ = 'market' if order_type == 'MKT' else 'limit'

        try:
            # 1. Place Parent Order
            params = {}
            if type_ == 'limit':
                 if not price: raise ValueError("Price needed for Limit")
                 order = await self.exchange.create_order(symbol, type_, side, quantity, price, params)
            else:
                 order = await self.exchange.create_order(symbol, type_, side, quantity, params=params)

            self.logger.info(f"Binance Entry Order Placed: {order['id']}")

            # 2. Place Stop Loss (Post-Fill logic for Spot)
            if stop_loss and action == 'BUY':
                try:
                    stop_params = {'stopPrice': stop_loss}
                    stop_order = await self.exchange.create_order(
                        symbol,
                        'STOP_LOSS_LIMIT',
                        'sell',
                        quantity,
                        stop_loss, # Limit Price
                        stop_params
                    )
                    self.logger.info(f"Binance Stop Loss Placed: {stop_order['id']}")
                except Exception as sl_e:
                    self.logger.critical(f"FAILED TO PLACE STOP LOSS for {symbol}: {sl_e}")
                    self.logger.warning("Attempting EMERGENCY CLOSE...")
                    try:
                        await self.exchange.create_order(symbol, 'market', 'sell', quantity)
                        self.logger.info("Emergency Close Successful.")
                    except Exception as close_e:
                        self.logger.critical(f"EMERGENCY CLOSE FAILED: {close_e}. MANUAL INTERVENTION REQUIRED!")

            if take_profit and action == 'BUY':
                self.logger.warning("Binance Connector: Take Profit order skipped to avoid locking assets for Stop Loss. Monitor manually.")

            class GenericTrade:
                def __init__(self, order_id):
                    self.order = type('obj', (object,), {'orderId': order_id})()

            return GenericTrade(order['id'])

        except Exception as e:
            self.logger.error(f"Binance Order Failed: {e}")
            raise

    async def get_account_summary(self):
        try:
            balance = await self.exchange.fetch_balance()
            total_usdt = float(balance['total'].get('USDT', 0))
            return {
                'NetLiquidation': total_usdt,
                'TotalCashValue': total_usdt
            }
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return {'NetLiquidation': 0}

    async def get_positions(self):
        try:
            balance = await self.exchange.fetch_balance()
            positions = []
            for asset, amount in balance['total'].items():
                if amount > 0 and asset != 'USDT':
                    positions.append({
                        'symbol': asset,
                        'position': amount,
                        'avgCost': 0
                    })
            return positions
        except Exception as e:
             return []
