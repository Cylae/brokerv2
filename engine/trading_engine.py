from ib_insync import Stock, MarketOrder, LimitOrder, util
import logging
import asyncio
import pandas as pd
from datetime import datetime
from .indicators import Indicators

class TradingEngine:
    def __init__(self, ib_connector):
        self.ib_connector = ib_connector
        self.ib = ib_connector.get_ib_instance()
        self.logger = logging.getLogger(__name__)

    async def get_market_data(self, symbol, exchange='SMART', currency='USD'):
        """Fetches a snapshot AND historical market data for a given symbol."""
        contract = Stock(symbol, exchange, currency)

        # Qualify the contract to ensure it exists and get details
        try:
            await self.ib.qualifyContractsAsync(contract)
        except Exception as e:
            self.logger.error(f"Could not qualify contract for {symbol}: {e}")
            return None

        # 1. Request Snapshot
        ticker = self.ib.reqMktData(contract, '', False, False)

        # Wait for data to populate (simple retry mechanism)
        for _ in range(50):
            if ticker.last or ticker.bid or ticker.ask:
                break
            await asyncio.sleep(0.1)

        snapshot = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'last': ticker.last,
            'bid': ticker.bid,
            'ask': ticker.ask,
            'volume': ticker.volume,
            'close': ticker.close
        }

        # 2. Request Historical Data (e.g., 2 days of 1-hour bars)
        # Note: 'TRADES' is usually better for stocks, but 'MIDPOINT' might be safer for forex.
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
                self.logger.warning(f"No historical data received for {symbol}")
                technicals = {}

        except Exception as e:
             self.logger.error(f"Failed to fetch historical data for {symbol}: {e}")
             technicals = {}

        # Merge Data
        return {**snapshot, **technicals}

    async def execute_order(self, symbol, action, quantity, order_type='MKT', price=None, stop_loss=None, take_profit=None):
        """
        Executes an order, optionally with Bracket (Stop Loss / Take Profit).
        """
        contract = Stock(symbol, 'SMART', 'USD')
        await self.ib.qualifyContractsAsync(contract)

        # Parent Order
        if order_type.upper() == 'MKT':
            parent = MarketOrder(action, quantity)
        elif order_type.upper() == 'LMT':
            if price is None:
                raise ValueError("Price must be provided for Limit orders.")
            parent = LimitOrder(action, quantity, price)
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        orders_to_place = [parent]

        # Bracket Logic (only if action is BUY for simplicity in this version)
        # For SELL orders, logic reverses (SL > Price, TP < Price)

        if (stop_loss or take_profit) and action == 'BUY':
            parent.transmit = False # Do not transmit until child orders are attached

            if stop_loss:
                stop = self.ib.bracketStopOrder(parent, stop_loss)
                stop.transmit = True # Last child transmits all
                if take_profit:
                    stop.transmit = False # Wait for TP
                orders_to_place.append(stop)

            if take_profit:
                limit = self.ib.bracketLimitOrder(parent, take_profit)
                limit.transmit = True
                orders_to_place.append(limit)

        # TODO: Handle Bracket for SELL (Short) orders if needed

        trades = []
        for o in orders_to_place:
            trade = self.ib.placeOrder(contract, o)
            trades.append(trade)

        self.logger.info(f"Placed {len(orders_to_place)} orders for {symbol}. Action: {action}")
        return trades[0] # Return parent trade

    async def get_account_summary(self):
        """Returns account summary."""
        tags = 'NetLiquidation,TotalCashValue,GrossPositionValue'
        summary = await self.ib.accountSummaryAsync()
        data = {}
        for item in summary:
             if item.tag in tags.split(','):
                 data[item.tag] = item.value
        return data

    async def get_positions(self):
        """Returns current positions."""
        positions = self.ib.positions()
        pos_list = []
        for p in positions:
            pos_list.append({
                'symbol': p.contract.symbol,
                'position': p.position,
                'avgCost': p.avgCost
            })
        return pos_list

    async def get_portfolio(self):
         """Returns portfolio details which includes unrealized PnL."""
         portfolio = self.ib.portfolio()
         port_list = []
         for p in portfolio:
             port_list.append({
                 'symbol': p.contract.symbol,
                 'position': p.position,
                 'marketPrice': p.marketPrice,
                 'marketValue': p.marketValue,
                 'averageCost': p.averageCost,
                 'unrealizedPNL': p.unrealizedPNL,
                 'realizedPNL': p.realizedPNL
             })
         return port_list
