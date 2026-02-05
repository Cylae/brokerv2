import pytest
from datetime import datetime
import pytz
from engine.market_utils import MarketSchedule

def test_market_hours_open():
    # Wednesday 10:00 AM ET
    dt = datetime(2023, 10, 25, 10, 0, 0)
    dt = pytz.timezone('US/Eastern').localize(dt)
    assert MarketSchedule.is_market_open(dt) is True

def test_market_hours_closed_weekend():
    # Saturday 10:00 AM ET
    dt = datetime(2023, 10, 28, 10, 0, 0)
    dt = pytz.timezone('US/Eastern').localize(dt)
    assert MarketSchedule.is_market_open(dt) is False

def test_market_hours_closed_premarket():
    # Wednesday 8:00 AM ET
    dt = datetime(2023, 10, 25, 8, 0, 0)
    dt = pytz.timezone('US/Eastern').localize(dt)
    assert MarketSchedule.is_market_open(dt) is False

def test_market_hours_closed_afterhours():
    # Wednesday 5:00 PM ET
    dt = datetime(2023, 10, 25, 17, 0, 0)
    dt = pytz.timezone('US/Eastern').localize(dt)
    assert MarketSchedule.is_market_open(dt) is False
