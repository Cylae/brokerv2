from abc import ABC, abstractmethod
from typing import List, Optional
from .models import MarketData, TradeResult, Position, AccountSummary

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
    async def check_connection(self) -> bool:
        """Check if connection is active."""
        pass

    @abstractmethod
    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch market data (Snapshot + Historical)."""
        pass

    @abstractmethod
    async def execute_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        order_type: str = 'MKT',
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> TradeResult:
        """Execute an order."""
        pass

    @abstractmethod
    async def get_account_summary(self) -> AccountSummary:
        """Return account summary."""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Return list of current positions."""
        pass
