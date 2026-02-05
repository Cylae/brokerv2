from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict

@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    last: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[float] = None
    indicators: Dict[str, float] = field(default_factory=dict)

@dataclass
class TradeResult:
    order_id: str
    symbol: str
    action: str
    quantity: float
    price: Optional[float] = None
    status: str = "SUBMITTED"
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Position:
    symbol: str
    quantity: float
    avg_cost: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0

@dataclass
class AccountSummary:
    net_liquidation: float
    total_cash: float
    currency: str = "USD"
