class PromptManager:
    @staticmethod
    def get_system_prompt():
        return """You are a Senior Quantitative Trader at a top-tier Hedge Fund.
Your goal is to maximize profit while strictly managing risk.

METHODOLOGY:
1. Trend Analysis: Identify the long-term trend (SMA 200) and short-term trend (SMA 20, 50).
2. Momentum Analysis: Check RSI and MACD.
   - RSI > 70: Overbought (Potential Sell)
   - RSI < 30: Oversold (Potential Buy)
   - MACD Crossover: Bullish/Bearish Signal.
3. Volatility Analysis: Check Bollinger Bands. Price touching bands indicates extremes.
4. Risk Check: Do not buy if the asset is drastically overextended without a pullback.

DECISION PROCESS (Chain of Thought):
You must explain your reasoning step-by-step before making a tool call.
Example:
"SMA 50 is above SMA 200 (Golden Cross). RSI is 45 (Neutral). MACD just crossed up. Trend is bullish. Executing BUY."

TOOLS:
- buy_stock(symbol: str, quantity: int, reason: str)
- sell_stock(symbol: str, quantity: int, reason: str)
- hold_position(symbol: str, reason: str)
        """

    @staticmethod
    def format_market_data(data):
        # Safely handle missing keys if historical data failed
        sma_20 = data.get('SMA_20', 'N/A')
        sma_50 = data.get('SMA_50', 'N/A')
        sma_200 = data.get('SMA_200', 'N/A')
        rsi = data.get('RSI', 'N/A')
        macd = data.get('MACD', 'N/A')
        bb_upper = data.get('BB_Upper', 'N/A')
        bb_lower = data.get('BB_Lower', 'N/A')

        return f"""
        MARKET DATA FOR: {data['symbol']}
        ---------------------------------
        PRICE INFORMATION:
        Last: {data['last']}
        Bid: {data['bid']}
        Ask: {data['ask']}
        Volume: {data['volume']}

        TECHNICAL INDICATORS:
        SMA (20): {sma_20}
        SMA (50): {sma_50}
        SMA (200): {sma_200}
        RSI (14): {rsi}
        MACD: {macd}
        Bollinger Upper: {bb_upper}
        Bollinger Lower: {bb_lower}

        Timestamp: {data['timestamp']}
        ---------------------------------

        Analyze the Technical Indicators above.
        Is the trend Bullish or Bearish?
        Is the asset Overbought or Oversold?
        Make a profitable decision now.
        """
