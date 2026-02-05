from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
import logging
import asyncio
from datetime import datetime
from .base_connector import BaseConnector
from .indicators import Indicators

class IBKRConnector(BaseConnector):
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.connected = False
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        if not self.ib.isConnected():
            try:
                self.logger.info(f"Connecting to IBKR at {self.host}:{self.port}...")
                await self.ib.connectAsync(self.host, self.port, self.client_id)
                self.connected = True
                self.logger.info("Connected to IBKR.")
            except Exception as e:
                self.logger.error(f"Failed to connect to IBKR: {e}")
                self.connected = False
                raise
        else:
            self.connected = True

    async def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()
            self.connected = False
            self.logger.info("Disconnected from IBKR.")

    async def check_connection(self):
        return self.ib.isConnected()

    async def get_market_data(self, symbol):
        contract = Stock(symbol, 'SMART', 'USD')
        try:
            await self.ib.qualifyContractsAsync(contract)
        except Exception as e:
            self.logger.error(f"Could not qualify contract for {symbol}: {e}")
            return None

        # 1. Snapshot
        ticker = self.ib.reqMktData(contract, '', False, False)
        for _ in range(50):
            if ticker.last or ticker.bid or ticker.ask:
                break
            await asyncio.sleep(0.1)

        snapshot = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'last': ticker.last if ticker.last else ticker.close, # Fallback to close if last missing
            'bid': ticker.bid,
            'ask': ticker.ask,
            'volume': ticker.volume,
            'close': ticker.close
        }

        # If still no price, fail
        if not snapshot['last']:
             self.logger.warning(f"No market data received for {symbol}")
             return None

        # 2. Historical Data for Indicators
        try:
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime='',
                durationStr='10 D',
                barSizeSetting='1 hour',
                whatToShow='TRADES',
                useRTH=True
            )
            if bars:
                df = util.df(bars)
                technicals = Indicators.get_technical_summary(df)
            else:
                technicals = {}
        except Exception as e:
            self.logger.error(f"Historical data error for {symbol}: {e}")
            technicals = {}

        return {**snapshot, **technicals}

    async def execute_order(self, symbol, action, quantity, order_type='MKT', price=None, stop_loss=None, take_profit=None):
        contract = Stock(symbol, 'SMART', 'USD')
        await self.ib.qualifyContractsAsync(contract)

        if order_type.upper() == 'MKT':
            parent = MarketOrder(action, quantity)
        elif order_type.upper() == 'LMT':
            if price is None:
                 raise ValueError("Price needed for LMT")
            parent = LimitOrder(action, quantity, price)
        else:
            raise ValueError(f"Unknown Order Type: {order_type}")

        orders_to_place = [parent]

        # Bracket Logic (Simple implementation for BUY)
        if (stop_loss or take_profit) and action == 'BUY':
            parent.transmit = False
            if stop_loss:
                stop = self.ib.bracketStopOrder(parent, stop_loss)
                stop.transmit = True
                if take_profit:
                    stop.transmit = False
                orders_to_place.append(stop)
            if take_profit:
                limit = self.ib.bracketLimitOrder(parent, take_profit)
                limit.transmit = True
                orders_to_place.append(limit)

        trades = []
        for o in orders_to_place:
            t = self.ib.placeOrder(contract, o)
            trades.append(t)

        # Return a simplified dict or specific object. For now returning the IB Trade object wrapper or similar.
        # But BaseConnector should return a generic structure ideally.
        # For MVP, let's return a simple object wrapper to decouple `main` from `ib_insync` types?
        # Actually `main.py` accesses `trade.order.orderId`.
        # Let's return a Mock-like object or the raw trade if we assume main knows IB?
        # To be purely generic, we should return a generic TradeResult.
        # But let's return the raw object for now and update Main later if needed.
        return trades[0]

    async def get_account_summary(self):
        tags = 'NetLiquidation,TotalCashValue,GrossPositionValue'
        summary = await self.ib.accountSummaryAsync()
        data = {}
        for item in summary:
             if item.tag in tags.split(','):
                 data[item.tag] = float(item.value)
        return data

    async def get_positions(self):
        positions = self.ib.positions()
        pos_list = []
        for p in positions:
            pos_list.append({
                'symbol': p.contract.symbol,
                'position': p.position,
                'avgCost': p.avgCost
            })
        return pos_list
