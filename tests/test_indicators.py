import pytest
import pandas as pd
import numpy as np
from engine.indicators import Indicators

@pytest.fixture
def sample_data():
    # Generate 300 data points for testing
    np.random.seed(42)
    # A simple random walk
    prices = [100.0]
    for _ in range(299):
        prices.append(prices[-1] + np.random.normal(0, 1))

    return pd.DataFrame({'close': prices})

def test_calculate_sma(sample_data):
    series = sample_data['close']
    sma = Indicators.calculate_sma(series, 20)
    assert len(sma) == len(series)
    assert pd.isna(sma.iloc[0])
    assert not pd.isna(sma.iloc[19])

    # Manual check for the first 20 elements
    manual_sma = series.iloc[:20].mean()
    assert np.isclose(sma.iloc[19], manual_sma)

def test_calculate_ema(sample_data):
    series = sample_data['close']
    ema = Indicators.calculate_ema(series, 20)
    assert len(ema) == len(series)
    assert not pd.isna(ema.iloc[0]) # ewm with adjust=False starts at first element

def test_calculate_rsi(sample_data):
    series = sample_data['close']
    rsi = Indicators.calculate_rsi(series, 14)
    assert len(rsi) == len(series)
    assert pd.isna(rsi.iloc[0])
    assert not pd.isna(rsi.iloc[14])
    # RSI must be between 0 and 100
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0).all()
    assert (valid_rsi <= 100).all()

def test_calculate_macd(sample_data):
    series = sample_data['close']
    macd, signal = Indicators.calculate_macd(series)
    assert len(macd) == len(series)
    assert len(signal) == len(series)
    assert not pd.isna(macd.iloc[-1])
    assert not pd.isna(signal.iloc[-1])

def test_calculate_bollinger_bands(sample_data):
    series = sample_data['close']
    upper, lower = Indicators.calculate_bollinger_bands(series, 20, 2)
    assert len(upper) == len(series)
    assert len(lower) == len(series)

    valid_upper = upper.dropna()
    valid_lower = lower.dropna()
    # Upper band should be greater than lower band
    assert (valid_upper >= valid_lower).all()

def test_get_technical_summary_empty_or_short():
    df_empty = pd.DataFrame()
    assert Indicators.get_technical_summary(df_empty) == {}

    df_short = pd.DataFrame({'close': [1, 2, 3]})
    assert Indicators.get_technical_summary(df_short) == {}

def test_get_technical_summary_success(sample_data):
    summary = Indicators.get_technical_summary(sample_data)

    assert "SMA_20" in summary
    assert "SMA_50" in summary
    assert "SMA_200" in summary
    assert "RSI" in summary
    assert "MACD" in summary
    assert "MACD_Signal" in summary
    assert "BB_Upper" in summary
    assert "BB_Lower" in summary
    assert "Close" in summary

    # Since we have 300 data points, SMA_200 should not be None
    assert summary["SMA_200"] is not None
    assert isinstance(summary["SMA_20"], float) or isinstance(summary["SMA_20"], np.floating)
    assert summary["Close"] == round(sample_data['close'].iloc[-1], 2)

def test_get_technical_summary_no_sma200():
    # Create DF with >50 but <200 rows
    np.random.seed(42)
    df = pd.DataFrame({'close': np.random.normal(100, 1, 100)})
    summary = Indicators.get_technical_summary(df)

    assert "SMA_20" in summary
    assert summary["SMA_200"] is None
