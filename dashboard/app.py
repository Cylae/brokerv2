import streamlit as st
import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.ib_connector import IBConnector
from engine.trading_engine import TradingEngine
from ai.ai_wrapper import AIWrapper
from config import Config

# Helper to run async functions
def run_async(coro):
    return asyncio.run(coro)

st.set_page_config(page_title="AI Trading System", layout="wide")
st.title("🤖 Autonomous Multi-Model AI Trading System")

# Sidebar for Config
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("OpenRouter API Key", type="password", value=Config.OPENROUTER_API_KEY)
model = st.sidebar.text_input("Model", value=Config.OPENROUTER_MODEL)
ib_host = st.sidebar.text_input("IB Host", value=Config.IB_HOST)
ib_port = st.sidebar.number_input("IB Port", value=Config.IB_PORT)
client_id = st.sidebar.number_input("Client ID", value=Config.IB_CLIENT_ID)

if 'ib_connector' not in st.session_state:
    st.session_state.ib_connector = None
if 'trading_engine' not in st.session_state:
    st.session_state.trading_engine = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")

# Connection Section
st.header("1. Connection Status")
col1, col2 = st.columns(2)

with col1:
    if st.button("Connect to IBKR"):
        try:
            connector = IBConnector(host=ib_host, port=ib_port, client_id=client_id)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(connector.connect())

            st.session_state.ib_connector = connector
            st.session_state.trading_engine = TradingEngine(connector)
            st.success("Connected to IBKR")
            log("Connected to IBKR")

        except Exception as e:
            st.error(f"Connection failed: {e}")
            log(f"Connection failed: {e}")

with col2:
    if st.session_state.ib_connector:
        st.write("Status: **Connected**")
        if st.button("Disconnect"):
            st.session_state.ib_connector.disconnect()
            st.session_state.ib_connector = None
            st.session_state.trading_engine = None
            st.warning("Disconnected")
            log("Disconnected")
    else:
        st.write("Status: **Disconnected**")

# Main Dashboard
if st.session_state.trading_engine:
    engine = st.session_state.trading_engine

    # Account Summary
    st.header("2. Account Summary")
    if st.button("Refresh Account"):
        try:
            summary = engine.ib.run(engine.get_account_summary())
            st.json(summary)

            positions = engine.ib.run(engine.get_positions())
            if positions:
                st.write("Positions:")
                st.dataframe(pd.DataFrame(positions))
            else:
                st.info("No positions.")
        except Exception as e:
            st.error(f"Error fetching account data: {e}")

    # Trading Section
    st.header("3. AI Auto-Trade")
    symbol = st.text_input("Symbol to Analyze", value="AAPL")

    if st.button("Analyze & Execute"):
        if not api_key:
            st.error("Please provide OpenRouter API Key")
        else:
            log(f"Starting analysis for {symbol}...")
            with st.spinner("Fetching Market Data..."):
                try:
                    # Fetch rich market data (Snapshot + Historical)
                    market_data = engine.ib.run(engine.get_market_data(symbol))

                    if market_data:
                        # Display Data & Indicators
                        st.subheader(f"Market Data & Technicals: {symbol}")

                        col_price, col_tech = st.columns(2)
                        with col_price:
                            st.metric("Last Price", market_data.get('last'))
                            st.metric("Volume", market_data.get('volume'))

                        with col_tech:
                            st.write("**Indicators**")
                            st.write(f"SMA 20: {market_data.get('SMA_20', 'N/A')}")
                            st.write(f"SMA 50: {market_data.get('SMA_50', 'N/A')}")
                            st.write(f"RSI: {market_data.get('RSI', 'N/A')}")
                            st.write(f"MACD: {market_data.get('MACD', 'N/A')}")
                            st.write(f"Bollinger: {market_data.get('BB_Upper', 'N/A')} / {market_data.get('BB_Lower', 'N/A')}")

                        st.json(market_data)

                        ai = AIWrapper(api_key, model)
                        with st.spinner("AI Thinking (Technical Analysis)..."):
                            decision = ai.analyze_and_decide(market_data)

                        if decision:
                            st.subheader("AI Decision")
                            st.write(f"**Action:** {decision['decision']}")
                            st.write(f"**Reason:** {decision['args'].get('reason', 'No reason provided')}")
                            st.write(f"**Quantity:** {decision['args'].get('quantity', 'N/A')}")

                            log(f"AI Decision for {symbol}: {decision['decision']}")

                            # Execution Logic
                            cmd = decision['decision']
                            args = decision['args']

                            if cmd == 'buy_stock':
                                with st.spinner("Executing Buy Order..."):
                                    trade = engine.ib.run(engine.execute_order(args['symbol'], 'BUY', args['quantity'], 'MKT'))
                                    st.success(f"Buy Order Placed: {trade}")
                                    log(f"Buy Order Placed: {args['quantity']} {args['symbol']}")

                            elif cmd == 'sell_stock':
                                with st.spinner("Executing Sell Order..."):
                                    trade = engine.ib.run(engine.execute_order(args['symbol'], 'SELL', args['quantity'], 'MKT'))
                                    st.success(f"Sell Order Placed: {trade}")
                                    log(f"Sell Order Placed: {args['quantity']} {args['symbol']}")

                            elif cmd == 'hold_position':
                                st.info("Holding position. No order placed.")
                                log(f"Hold decision for {symbol}")

                        else:
                            st.error("AI failed to make a decision.")
                    else:
                        st.error("Failed to fetch market data.")
                except Exception as e:
                     st.error(f"Error during execution: {e}")
                     log(f"Error: {e}")

# Logs
st.header("4. System Logs")
for l in reversed(st.session_state.logs):
    st.text(l)
