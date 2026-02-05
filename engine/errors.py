class TradingSystemError(Exception):
    """Base class for exceptions in this module."""
    pass

class ConnectionError(TradingSystemError):
    """Raised when connection to exchange/broker fails."""
    pass

class MarketDataError(TradingSystemError):
    """Raised when market data cannot be fetched."""
    pass

class OrderError(TradingSystemError):
    """Raised when an order fails to execute."""
    pass

class ConfigurationError(TradingSystemError):
    """Raised when configuration is invalid."""
    pass
