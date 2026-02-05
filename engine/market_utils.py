from datetime import datetime, time
import pytz

class MarketSchedule:
    TIMEZONE = pytz.timezone('US/Eastern')
    OPEN_TIME = time(9, 30)
    CLOSE_TIME = time(16, 0)

    @staticmethod
    def is_market_open(current_time=None):
        """
        Checks if the US stock market is currently open.
        """
        if current_time is None:
            current_time = datetime.now(MarketSchedule.TIMEZONE)
        else:
            # Ensure provided time is aware, if not assume UTC and convert
            if current_time.tzinfo is None:
                 current_time = pytz.utc.localize(current_time).astimezone(MarketSchedule.TIMEZONE)
            else:
                 current_time = current_time.astimezone(MarketSchedule.TIMEZONE)

        # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
        if current_time.weekday() >= 5:
            return False

        # Check time bounds
        current_time_time = current_time.time()
        if MarketSchedule.OPEN_TIME <= current_time_time <= MarketSchedule.CLOSE_TIME:
            return True

        return False
