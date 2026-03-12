import ccxt.async_support as ccxt
import logging
import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Optional
from .base_connector import BaseConnector
from .indicators import Indicators
from .models import MarketData, TradeResult, Position, AccountSummary

class CCXTConnector(BaseConnector):
    def __init__(self, api_key: str, secret_key: str, passphrase: str = None, exchange_id: str = 'binance', testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.exchange_id = exchange_id.lower()
        self.testnet = testnet
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.exchange = None

        self._historical_cache = {}
        self._historical_cache_ttl = 300  # 5 minutes

        # Initialize Exchange
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            config = {
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            if passphrase:
                config['password'] = passphrase

            self.exchange = exchange_class(config)

            if testnet:
                self.exchange.set_sandbox_mode(True)

        except AttributeError:
            self.logger.error(f"Exchange '{self.exchange_id}' not found in ccxt.")
            raise ValueError(f"Exchange '{self.exchange_id}' not supported.")

    async def connect(self):
        try:
            await self.exchange.load_markets()
            self.connected = True
            self.logger.info(f"Connected to {self.exchange_id.capitalize()}.")
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.exchange_id}: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        if self.exchange:
            await self.exchange.close()
            self.connected = False
            self.logger.info(f"Disconnected from {self.exchange_id}.")

    async def check_connection(self) -> bool:
        return self.connected

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        # Standardization Logic
        if '/' not in symbol and len(symbol) <= 5:
                symbol = f"{symbol}/USDT"

        try:
            # Check historical cache
            current_time = asyncio.get_event_loop().time()
            cached_data = self._historical_cache.get(symbol)

            technicals = {}
            if cached_data and (current_time - cached_data['time'] < self._historical_cache_ttl):
                bars_task = None
                technicals = cached_data['technicals']
            else:
                bars_task = self.exchange.fetch_ohlcv(symbol, '1h', limit=100)

            # Concurrent Fetch with error handling
            try:
                ticker_task = self.exchange.fetch_ticker(symbol)
                if bars_task:
                    ticker, bars = await asyncio.gather(ticker_task, bars_task)
                else:
                    ticker = await ticker_task
                    bars = None
            except Exception as fetch_err:
                self.logger.error(f"API fetch error for {symbol}: {fetch_err}")
                return None

            if bars:
                df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                technicals = Indicators.get_technical_summary(df)
                self._historical_cache[symbol] = {
                    'time': current_time,
                    'technicals': technicals
                }

            return MarketData(
                symbol=symbol,
                timestamp=datetime.now(),
                last=ticker['last'],
                bid=ticker['bid'],
                ask=ticker['ask'],
                volume=ticker.get('baseVolume', ticker.get('quoteVolume', 0)),
                indicators=technicals
            )

        except Exception as e:
            self.logger.error(f"Error processing data for {symbol} on {self.exchange_id}: {e}")
            return None

    async def execute_order(self, symbol: str, action: str, quantity: float, order_type: str = 'MKT', price: float = None, stop_loss: float = None, take_profit: float = None) -> TradeResult:
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"

        side = action.lower()
        type_ = 'market' if order_type == 'MKT' else 'limit'

        # Ensure quantity is precise enough for the exchange but not too precise
        # (Ideally should use exchange.amount_to_precision, but keeping it simple for now)

        try:
            # 1. Place Parent Order
            params = {}
            if type_ == 'limit':
                 if not price: raise ValueError("Price needed for Limit")
                 order = await self.exchange.create_order(symbol, type_, side, quantity, price, params)
            else:
                 order = await self.exchange.create_order(symbol, type_, side, quantity, params=params)

            self.logger.info(f"Entry Order Placed on {self.exchange_id}: {order['id']}")

            executed_price = order.get('price') or order.get('average') or price

            # 2. Place Stop Loss
            if stop_loss and action == 'BUY':
                await self._place_stop_loss(symbol, quantity, stop_loss, executed_price)

            return TradeResult(
                order_id=str(order['id']),
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=executed_price,
                status=order['status'].upper(),
                asset_type="CRYPTO"
            )

        except Exception as e:
            self.logger.error(f"Order Failed on {self.exchange_id}: {e}")
            raise

    async def _place_stop_loss(self, symbol, quantity, stop_price, entry_price):
        """
        Attempts to place a stop loss order.
        Handles exchange-specific quirks where possible.
        """
        try:
            params = {}
            # Binance specific
            if self.exchange_id == 'binance':
                params['stopPrice'] = stop_price
                order = await self.exchange.create_order(
                    symbol,
                    'STOP_LOSS_LIMIT', # Binance uses this for OCO-like behavior or just stop limit
                    'sell',
                    quantity,
                    stop_price, # Limit Price (same as stop for simplicity, or slightly lower)
                    params
                )
                self.logger.info(f"Stop Loss (Binance) Placed: {order['id']}")

            else:
                # Generic fallback (Coinbase, Kraken, etc.)
                # Many support 'stop' type with 'price' as stop trigger
                # Or 'stop_loss' type.
                # CCXT unifies this somewhat.

                # Attempt 1: Standard 'stop' order
                try:
                    params['stopPrice'] = stop_price
                    # Some exchanges require triggerPrice
                    params['triggerPrice'] = stop_price

                    order = await self.exchange.create_order(
                        symbol,
                        'stop_market', # More likely to execute than stop limit
                        'sell',
                        quantity,
                        None, # No price for market
                        params
                    )
                    self.logger.info(f"Stop Loss (Generic Market) Placed: {order['id']}")
                except Exception as ex1:
                     self.logger.warning(f"Generic Stop Market failed: {ex1}. Trying Stop Limit...")
                     # Attempt 2: Stop Limit
                     order = await self.exchange.create_order(
                        symbol,
                        'stop_limit',
                        'sell',
                        quantity,
                        stop_price, # Limit Price
                        params
                    )
                     self.logger.info(f"Stop Loss (Generic Limit) Placed: {order['id']}")

        except Exception as sl_e:
            self.logger.critical(f"FAILED TO PLACE STOP LOSS for {symbol} on {self.exchange_id}: {sl_e}")
            self.logger.warning("Attempting EMERGENCY CLOSE...")
            try:
                await self.exchange.create_order(symbol, 'market', 'sell', quantity)
                self.logger.info("Emergency Close Successful.")
            except Exception as close_e:
                self.logger.critical(f"EMERGENCY CLOSE FAILED: {close_e}. MANUAL INTERVENTION REQUIRED!")

    async def get_account_summary(self) -> AccountSummary:
        try:
            balance = await self.exchange.fetch_balance()
            # Try to get total in USDT or USD
            total = 0.0
            if 'total' in balance:
                total = float(balance['total'].get('USDT', balance['total'].get('USD', 0)))

            return AccountSummary(
                net_liquidation=total,
                total_cash=total, # Approx for crypto
                currency="USDT"
            )
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return AccountSummary(0.0, 0.0, "USDT")

    async def get_positions(self) -> List[Position]:
        try:
            balance = await self.exchange.fetch_balance()
            positions = []

            # balance['total'] is a dict of {currency: amount}
            if 'total' in balance:
                for asset, amount in balance['total'].items():
                    # Filter dust
                    if amount > 0.0001 and asset not in ['USDT', 'USD']:
                        positions.append(Position(
                            symbol=f"{asset}/USDT", # Assumption
                            quantity=amount,
                            avg_cost=0.0, # Not always available
                            asset_type="CRYPTO"
                        ))
            return positions
        except Exception as e:
             self.logger.error(f"Error fetching positions: {e}")
             return []
