from ib_insync import Stock, MarketOrder, LimitOrder
import logging
import asyncio
import pandas as pd
from datetime import datetime

class TradingEngine:
    def __init__(self, ib_connector):
        self.ib_connector = ib_connector
        self.ib = ib_connector.get_ib_instance()
        self.logger = logging.getLogger(__name__)

    async def get_market_data(self, symbol, exchange='SMART', currency='USD'):
        """Fetches a snapshot of market data for a given symbol."""
        contract = Stock(symbol, exchange, currency)

        # Qualify the contract to ensure it exists and get details
        try:
            await self.ib.qualifyContractsAsync(contract)
        except Exception as e:
            self.logger.error(f"Could not qualify contract for {symbol}: {e}")
            return None

        # Request market data
        ticker = self.ib.reqMktData(contract, '', False, False)

        # Wait for data to populate (simple retry mechanism)
        for _ in range(50):
            if ticker.last or ticker.bid or ticker.ask:
                break
            await asyncio.sleep(0.1)

        if not (ticker.last or ticker.bid or ticker.ask):
             self.logger.warning(f"No market data received for {symbol}")
             # We might still return what we have, or None

        data = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'last': ticker.last,
            'bid': ticker.bid,
            'ask': ticker.ask,
            'volume': ticker.volume,
            'close': ticker.close
        }
        return data

    async def execute_order(self, symbol, action, quantity, order_type='MKT', price=None):
        """Executes an order."""
        contract = Stock(symbol, 'SMART', 'USD')
        await self.ib.qualifyContractsAsync(contract)

        if order_type.upper() == 'MKT':
            order = MarketOrder(action, quantity)
        elif order_type.upper() == 'LMT':
            if price is None:
                raise ValueError("Price must be provided for Limit orders.")
            order = LimitOrder(action, quantity, price)
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        trade = self.ib.placeOrder(contract, order)
        self.logger.info(f"Order placed: {action} {quantity} {symbol} @ {order_type} {price if price else ''}")
        return trade

    async def get_account_summary(self):
        """Returns account summary."""
        # Using accountSummary or accountValues
        # For simplicity, let's use accountValues for now or wrapper's accountSummary
        # ib_insync makes it easy with managed accounts
        tags = 'NetLiquidation,TotalCashValue,GrossPositionValue'
        summary = await self.ib.accountSummaryAsync()
        # Filter for our account if necessary, but typically returns list of AccountValue
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
