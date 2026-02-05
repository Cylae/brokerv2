import streamlit as st
import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.ib_connector import IBKRConnector
from engine.binance_connector import BinanceConnector
from ai.ai_wrapper import AIWrapper
from config import Config

# Helper to run async functions
def run_async(coro):
    return asyncio.run(coro)

st.set_page_config(page_title="AI Trading System", layout="wide")
st.title("🤖 Autonomous Multi-Model AI Trading System")

# Sidebar for Config
st.sidebar.header("Configuration")

# 1. Trading Mode Selector
trading_mode = st.sidebar.radio("Trading Mode", ("IBKR (Stocks)", "Binance (Crypto)"))

api_key = st.sidebar.text_input("OpenRouter API Key", type="password", value=Config.OPENROUTER_API_KEY)
model = st.sidebar.text_input("AI Model", value=Config.OPENROUTER_MODEL)

connector = None

# Conditional Inputs
if trading_mode == "IBKR (Stocks)":
    st.sidebar.subheader("IBKR Settings")
    ib_host = st.sidebar.text_input("IB Host", value=Config.IB_HOST)
    ib_port = st.sidebar.number_input("IB Port", value=Config.IB_PORT)
    client_id = st.sidebar.number_input("Client ID", value=Config.IB_CLIENT_ID)

    if st.button("Connect to IBKR"):
        try:
            connector = IBKRConnector(host=ib_host, port=ib_port, client_id=client_id)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(connector.connect())
            st.session_state.connector = connector
            st.session_state.mode = 'IBKR'
            st.success("Connected to IBKR")
        except Exception as e:
            st.error(f"IBKR Connection failed: {e}")

else: # Binance
    st.sidebar.subheader("Binance Settings")
    bin_key = st.sidebar.text_input("Binance API Key", value=Config.BINANCE_API_KEY, type="password")
    bin_secret = st.sidebar.text_input("Binance Secret", value=Config.BINANCE_SECRET_KEY, type="password")
    testnet = st.sidebar.checkbox("Testnet", value=Config.BINANCE_TESTNET)

    if st.button("Connect to Binance"):
        try:
            connector = BinanceConnector(api_key=bin_key, secret_key=bin_secret, testnet=testnet)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(connector.connect())
            st.session_state.connector = connector
            st.session_state.mode = 'BINANCE'
            st.success("Connected to Binance")
        except Exception as e:
            st.error(f"Binance Connection failed: {e}")

if 'connector' not in st.session_state:
    st.session_state.connector = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")

# Main Logic
if st.session_state.connector:
    if st.session_state.connector.connected:
        # Use connector directly as engine
        engine = st.session_state.connector

        # Disconnect Button
        if st.sidebar.button("Disconnect"):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(engine.disconnect())
            st.session_state.connector = None
            st.rerun()

    else:
        st.warning("Connector initialized but not connected.")

# Dashboard View
if st.session_state.connector and st.session_state.connector.connected:
    engine = st.session_state.connector

    # Account Summary
    st.header("2. Account Summary")
    if st.button("Refresh Account"):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            summary = loop.run_until_complete(engine.get_account_summary())
            st.json(summary)

            positions = loop.run_until_complete(engine.get_positions())
            if positions:
                st.write("Positions:")
                st.dataframe(pd.DataFrame(positions))
            else:
                st.info("No positions.")
        except Exception as e:
            st.error(f"Error fetching account data: {e}")

    # Trading Section
    st.header("3. AI Auto-Trade")
    default_sym = "AAPL" if st.session_state.mode == 'IBKR' else "BTC/USDT"
    symbol = st.text_input("Symbol to Analyze", value=default_sym)

    if st.button("Analyze & Execute"):
        if not api_key:
            st.error("Please provide OpenRouter API Key")
        else:
            log(f"Starting analysis for {symbol}...")
            with st.spinner("Fetching Market Data..."):
                try:
                    # New Loop for this action to avoid conflicts
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    market_data = loop.run_until_complete(engine.get_market_data(symbol))

                    if market_data:
                        # Display Data & Indicators
                        st.subheader(f"Market Data: {symbol}")
                        col_price, col_tech = st.columns(2)
                        with col_price:
                            st.metric("Last Price", market_data.get('last'))
                            st.metric("Volume", market_data.get('volume'))

                        with col_tech:
                            st.write("**Indicators**")
                            st.write(f"SMA 20: {market_data.get('SMA_20', 'N/A')}")
                            st.write(f"RSI: {market_data.get('RSI', 'N/A')}")
                            st.write(f"MACD: {market_data.get('MACD', 'N/A')}")
                            st.write(f"Bollinger: {market_data.get('BB_Upper', 'N/A')} / {market_data.get('BB_Lower', 'N/A')}")

                        ai = AIWrapper(api_key, model)
                        with st.spinner("AI Thinking..."):
                            decision = loop.run_until_complete(ai.analyze_and_decide(market_data))

                        if decision:
                            st.subheader("AI Decision")
                            st.write(f"**Action:** {decision['decision']}")
                            st.write(f"**Reason:** {decision['args'].get('reason', 'No reason provided')}")

                            log(f"AI Decision: {decision['decision']}")

                            # Execution Logic
                            cmd = decision['decision']
                            args = decision['args']

                            if cmd == 'buy_stock':
                                with st.spinner("Executing Buy Order..."):
                                    # Need explicit loop run
                                    loop.run_until_complete(engine.execute_order(
                                        args['symbol'], 'BUY', args['quantity'], 'MKT',
                                        stop_loss=args.get('stop_loss'),
                                        take_profit=args.get('take_profit')
                                    ))
                                    st.success(f"Buy Order Placed for {args['symbol']}")
                                    log(f"Buy Order Placed: {args['quantity']} {args['symbol']}")

                            elif cmd == 'sell_stock':
                                with st.spinner("Executing Sell Order..."):
                                    loop.run_until_complete(engine.execute_order(
                                        args['symbol'], 'SELL', args['quantity'], 'MKT',
                                        stop_loss=args.get('stop_loss')
                                    ))
                                    st.success(f"Sell Order Placed for {args['symbol']}")
                                    log(f"Sell Order Placed: {args['quantity']} {args['symbol']}")

                            elif cmd == 'hold_position':
                                st.info("Holding position.")
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
