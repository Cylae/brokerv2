from datetime import datetime, time
import pytz
from config import Config

class MarketSchedule:
    TIMEZONE = pytz.timezone('US/Eastern')
    OPEN_TIME = time(9, 30)
    CLOSE_TIME = time(16, 0)

    @staticmethod
    def is_market_open(current_time=None):
        """
        Checks if the market is currently open.
        Crypto (Binance) is always open.
        Stocks (IBKR) follow NYSE hours.
        """
        if Config.TRADING_MODE == 'BINANCE':
            return True

        if current_time is None:
            current_time = datetime.now(MarketSchedule.TIMEZONE)
        else:
            if current_time.tzinfo is None:
                 current_time = pytz.utc.localize(current_time).astimezone(MarketSchedule.TIMEZONE)
            else:
                 current_time = current_time.astimezone(MarketSchedule.TIMEZONE)

        if current_time.weekday() >= 5:
            return False

        current_time_time = current_time.time()
        if MarketSchedule.OPEN_TIME <= current_time_time <= MarketSchedule.CLOSE_TIME:
            return True

        return False
