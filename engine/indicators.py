import pandas as pd
import numpy as np

class Indicators:
    @staticmethod
    def calculate_sma(series, period):
        return series.rolling(window=period).mean()

    @staticmethod
    def calculate_ema(series, period):
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(series, fast=12, slow=26, signal=9):
        exp1 = Indicators.calculate_ema(series, fast)
        exp2 = Indicators.calculate_ema(series, slow)
        macd = exp1 - exp2
        signal_line = Indicators.calculate_ema(macd, signal)
        return macd, signal_line

    @staticmethod
    def calculate_bollinger_bands(series, period=20, std_dev=2):
        sma = Indicators.calculate_sma(series, period)
        std = series.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, lower

    @staticmethod
    def get_technical_summary(df):
        """
        Expects a DataFrame with a 'close' column.
        Returns a dictionary of the latest indicators.
        """
        if df.empty or len(df) < 50:
            return {}

        close = df['close']

        # Calculate Indicators
        sma_20 = Indicators.calculate_sma(close, 20)
        sma_50 = Indicators.calculate_sma(close, 50)
        sma_200 = Indicators.calculate_sma(close, 200)
        rsi = Indicators.calculate_rsi(close)
        macd, macd_signal = Indicators.calculate_macd(close)
        bb_upper, bb_lower = Indicators.calculate_bollinger_bands(close)

        # Get latest values
        return {
            "SMA_20": round(sma_20.iloc[-1], 2),
            "SMA_50": round(sma_50.iloc[-1], 2),
            "SMA_200": round(sma_200.iloc[-1], 2) if len(df) > 200 else None,
            "RSI": round(rsi.iloc[-1], 2),
            "MACD": round(macd.iloc[-1], 2),
            "MACD_Signal": round(macd_signal.iloc[-1], 2),
            "BB_Upper": round(bb_upper.iloc[-1], 2),
            "BB_Lower": round(bb_lower.iloc[-1], 2),
            "Close": round(close.iloc[-1], 2)
        }
