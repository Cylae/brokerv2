from abc import ABC, abstractmethod

class BaseConnector(ABC):
    @abstractmethod
    async def connect(self):
        """Connect to the exchange/broker."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from the exchange/broker."""
        pass

    @abstractmethod
    async def check_connection(self):
        """Check if connection is active."""
        pass

    @abstractmethod
    async def get_market_data(self, symbol):
        """
        Fetch market data (Snapshot + Historical).
        Should return a dictionary with:
        {
            'symbol': str,
            'timestamp': datetime,
            'last': float,
            'bid': float,
            'ask': float,
            'volume': float,
            'SMA_20': float,
            ... (other indicators)
        }
        """
        pass

    @abstractmethod
    async def execute_order(self, symbol, action, quantity, order_type='MKT', price=None, stop_loss=None, take_profit=None):
        """
        Execute an order.
        Returns a Trade object or Dictionary with order details.
        """
        pass

    @abstractmethod
    async def get_account_summary(self):
        """Return account summary (NetLiquidation, etc)."""
        pass

    @abstractmethod
    async def get_positions(self):
        """Return list of current positions."""
        pass
