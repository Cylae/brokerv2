import logging

class TradingEngine:
    def __init__(self, connector):
        self.connector = connector
        self.logger = logging.getLogger(__name__)

    async def get_market_data(self, symbol):
        """Fetches market data using the connector."""
        return await self.connector.get_market_data(symbol)

    async def execute_order(self, symbol, action, quantity, order_type='MKT', price=None, stop_loss=None, take_profit=None):
        """Executes an order using the connector."""
        return await self.connector.execute_order(symbol, action, quantity, order_type, price, stop_loss, take_profit)

    async def get_account_summary(self):
        """Returns account summary."""
        return await self.connector.get_account_summary()

    async def get_positions(self):
        """Returns current positions."""
        return await self.connector.get_positions()
