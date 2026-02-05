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

        # OPTIMIZATION: Reduce duration from 10 D to 2 D (48 bars).
        # Enough for SMA 20, but not SMA 50 or 200.
        # Wait, if we want SMA 50/200, we need history.
        # Let's check `Indicators.py`. It calculates SMA 20, 50, 200.
        # If we optimize speed, we might sacrifice long-term SMA accuracy or fetch it once.
        # For "Efficient" optimization request, let's assume accuracy > pure speed, but parallel fetch helps.
        # IBKR reqMktData is streaming/subscription based usually, but here we use snapshot.
        # We can run reqMktData and reqHistoricalDataAsync in parallel tasks.

        # Task 1: Snapshot
        async def get_snapshot():
            ticker = self.ib.reqMktData(contract, '', False, False)
            for _ in range(20): # Reduce wait loops
                if ticker.last or ticker.bid or ticker.ask:
                    break
                await asyncio.sleep(0.05)
            return ticker

        # Task 2: History (Keep 10 D for full indicator support, but parallelize)
        async def get_history():
            return await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime='',
                durationStr='10 D',
                barSizeSetting='1 hour',
                whatToShow='TRADES',
                useRTH=True
            )

        ticker, bars = await asyncio.gather(get_snapshot(), get_history())

        snapshot = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'last': ticker.last if ticker.last else ticker.close,
            'bid': ticker.bid,
            'ask': ticker.ask,
            'volume': ticker.volume,
            'close': ticker.close
        }

        if not snapshot['last']:
             self.logger.warning(f"No market data received for {symbol}")
             return None

        technicals = {}
        if bars:
            df = util.df(bars)
            technicals = Indicators.get_technical_summary(df)

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
