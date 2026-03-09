import pytest
from unittest.mock import patch, MagicMock
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

def test_market_open_crypto_mode():
    with patch('engine.market_utils.Config') as mock_config:
        mock_config.TRADING_MODE = 'BINANCE'
        assert MarketSchedule.is_market_open() is True

def test_market_open_current_time_none():
    with patch('engine.market_utils.Config') as mock_config:
        mock_config.TRADING_MODE = 'IBKR'
        # Mock datetime.now to return a specific time
        with patch('engine.market_utils.datetime') as mock_dt:
            # Monday 10:00 AM EST
            mock_dt.now.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=pytz.timezone('US/Eastern'))
            assert MarketSchedule.is_market_open() is True

def test_market_open_current_time_with_tz():
    with patch('engine.market_utils.Config') as mock_config:
        mock_config.TRADING_MODE = 'IBKR'
        # Pass a localized datetime object
        dt = pytz.timezone('Europe/London').localize(datetime(2023, 10, 2, 15, 0)) # 15:00 London = 10:00 EST
        assert MarketSchedule.is_market_open(dt) is True


def test_market_open_current_time_with_no_tz():
    with patch('engine.market_utils.Config') as mock_config:
        mock_config.TRADING_MODE = 'IBKR'
        # Pass a naive datetime object
        dt = datetime(2023, 10, 2, 10, 0) # Naive
        assert MarketSchedule.is_market_open(dt) is False
