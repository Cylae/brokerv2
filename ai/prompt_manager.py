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
4. Risk Management (CRITICAL):
   - You MUST define a STOP LOSS price for every trade.
   - Calculate Stop Loss based on support levels or ATR (if available), or just below recent lows.
   - Define a Take Profit target (usually 2x the risk distance).

DECISION PROCESS (Chain of Thought):
You must explain your reasoning step-by-step before making a tool call.
Example:
"SMA 50 is above SMA 200. RSI is 45. Trend is bullish. Support is at 145. I will buy with Stop Loss at 144.50."

TOOLS:
- buy_stock(symbol, quantity, stop_loss, take_profit, reason)
- sell_stock(symbol, quantity, stop_loss, reason)
- hold_position(symbol, reason)
        """

    @staticmethod
    def format_market_data(data):
        # Safely handle missing keys
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
        Where is the Stop Loss level?
        Make a profitable decision now.
        """
