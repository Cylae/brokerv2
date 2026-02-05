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
    def __init__(self, api_key: str, secret_key: str, exchange_id: str = 'binance', testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.exchange_id = exchange_id.lower()
        self.testnet = testnet

        # Initialize Exchange
        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class({
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
            self.logger.info(f"Connected to {self.exchange_id.capitalize()}.")
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.exchange_id}: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        await self.exchange.close()
        self.connected = False
        self.logger.info(f"Disconnected from {self.exchange_id}.")

    async def check_connection(self) -> bool:
        return self.connected

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        # Standardization Logic: Append /USDT only if no pair is specified
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"

        try:
            # Concurrent Fetch
            ticker_task = self.exchange.fetch_ticker(symbol)
            bars_task = self.exchange.fetch_ohlcv(symbol, '1h', limit=100)

            ticker, bars = await asyncio.gather(ticker_task, bars_task)

            technicals = {}
            if bars:
                df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                technicals = Indicators.get_technical_summary(df)

            return MarketData(
                symbol=symbol,
                timestamp=datetime.now(),
                last=ticker['last'],
                bid=ticker['bid'],
                ask=ticker['ask'],
                volume=ticker['baseVolume'],
                indicators=technicals
            )

        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol} on {self.exchange_id}: {e}")
            return None

    async def execute_order(self, symbol: str, action: str, quantity: float, order_type: str = 'MKT', price: float = None, stop_loss: float = None, take_profit: float = None) -> TradeResult:
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

            self.logger.info(f"Entry Order Placed: {order['id']}")

            # 2. Place Stop Loss (Simplified Logic)
            if stop_loss and action == 'BUY':
                try:
                    # Generic stop loss logic often differs by exchange.
                    # For generic support, we rely on basic 'STOP_LOSS_LIMIT' or similar if supported.
                    # This implementation targets Binance semantics primarily but fits generic CCXT structure.
                    stop_params = {'stopPrice': stop_loss}
                    stop_order = await self.exchange.create_order(
                        symbol,
                        'STOP_LOSS_LIMIT',
                        'sell',
                        quantity,
                        stop_loss, # Limit Price
                        stop_params
                    )
                    self.logger.info(f"Stop Loss Placed: {stop_order['id']}")
                except Exception as sl_e:
                    self.logger.critical(f"FAILED TO PLACE STOP LOSS for {symbol}: {sl_e}")
                    self.logger.warning("Attempting EMERGENCY CLOSE...")
                    try:
                        await self.exchange.create_order(symbol, 'market', 'sell', quantity)
                        self.logger.info("Emergency Close Successful.")
                    except Exception as close_e:
                        self.logger.critical(f"EMERGENCY CLOSE FAILED: {close_e}. MANUAL INTERVENTION REQUIRED!")

            return TradeResult(
                order_id=str(order['id']),
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price if price else order.get('price', order.get('average', 0.0)),
                status=order['status'].upper()
            )

        except Exception as e:
            self.logger.error(f"Order Failed: {e}")
            raise

    async def get_account_summary(self) -> AccountSummary:
        try:
            balance = await self.exchange.fetch_balance()
            total_equity = 0.0

            # Sum up major stablecoins and USD to get "Net Liquidation" approximation
            # This is a simplification. Ideally, we'd fetch ticker prices for all assets and sum them up.
            for currency in ['USD', 'USDT', 'USDC', 'EUR']:
                 total_equity += float(balance.get('total', {}).get(currency, 0))

            return AccountSummary(
                net_liquidation=total_equity,
                total_cash=total_equity,
                currency="USD" # Reporting in USD equivalent
            )
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return AccountSummary(0.0, 0.0)

    async def get_positions(self) -> List[Position]:
        try:
            balance = await self.exchange.fetch_balance()
            positions = []
            for asset, amount in balance.get('total', {}).items():
                # Filter out dust and standard quote currencies to show only "Positions"
                if amount > 0.00000001 and asset not in ['USD', 'USDT', 'USDC']:
                    positions.append(Position(
                        symbol=asset,
                        quantity=amount,
                        avg_cost=0.0 # CCXT spot doesn't track this easily
                    ))
            return positions
        except Exception as e:
             return []
