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
            # We need to run connect in a loop, but Streamlit is weird with asyncio.
            # For ib_insync in streamlit, it's best to use `ib.connect()` (blocking) instead of async if possible,
            # or manage the loop carefully. IBConnector uses `connectAsync`.
            # Let's try blocking connect for simplicity or wrap in run_async.

            # Since IBConnector uses connectAsync, we wrap it.
            # But wait, ib_insync `IB` object needs a live event loop for some operations.
            # Using `util.startLoop()` might be needed.
            from ib_insync import util
            # util.startLoop() # This might conflict with Streamlit's loop if any.

            # Simplified approach: Create a new loop for each action is bad for subscriptions.
            # Ideally we want a persistent connection.
            # For this MVP, let's assume we re-connect or check connection.

            # Actually, `ib_insync` can be used synchronously if we use `ib.connect()` instead of `connectAsync`.
            # Let's modify IBConnector usage or just call underlying sync methods if needed.
            # But my IBConnector is async.

            # Let's use `asyncio.new_event_loop().run_until_complete(...)` pattern carefully.

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
        # We need to run async command on the loop used by IB
        # This is tricky in Streamlit.
        # ib_insync.IB instance is attached to a loop.
        # If that loop is closed or we are in a different thread, it fails.

        # A workaround for Streamlit + ib_insync:
        # Re-use the loop or use `ib.run(coroutine)` if `ib` manages the loop.
        # `ib.run()` is a helper to run a coroutine.

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
                    market_data = engine.ib.run(engine.get_market_data(symbol))
                    if market_data:
                        st.subheader("Market Data")
                        st.json(market_data)

                        ai = AIWrapper(api_key, model)
                        with st.spinner("AI Thinking..."):
                            decision = ai.analyze_and_decide(market_data)

                        if decision:
                            st.subheader("AI Decision")
                            st.write(f"**Action:** {decision['decision']}")
                            st.write(f"**Arguments:** {decision['args']}")

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
