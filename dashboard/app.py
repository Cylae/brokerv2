import streamlit as st
import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.ib_connector import IBKRConnector
from engine.ccxt_connector import CCXTConnector
from engine.portfolio_manager import PortfolioManager
from engine.async_utils import get_or_create_event_loop
from ai.ai_wrapper import AIWrapper
from config import Config

st.set_page_config(page_title="AI Trading System", layout="wide")

# --- AUTHENTICATION LOGIC ---
def check_login():
    """Returns True if authenticated or no auth required."""
    if not Config or not Config.DASHBOARD_USERNAME or not Config.DASHBOARD_PASSWORD:
        return True # No Auth configured

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Show Login Form
    st.title("🔐 Login Required")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username == Config.DASHBOARD_USERNAME and password == Config.DASHBOARD_PASSWORD.get_secret_value():
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials")

    return False

# Stop execution if not logged in
if not check_login():
    st.stop()

# --- MAIN APP ---
st.title("🤖 Autonomous Multi-Model AI Trading System")

st.sidebar.header("Configuration")

# Trading Mode
trading_mode = st.sidebar.radio("Trading Mode", ("IBKR (Stocks)", "Crypto (Generic)", "Unified Portfolio"))

# Logout Button (Only if auth enabled)
if Config and Config.DASHBOARD_USERNAME:
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

api_key = st.sidebar.text_input("OpenRouter API Key", type="password", value=Config.OPENROUTER_KEY.get_secret_value() if Config and Config.OPENROUTER_KEY else "")
model = st.sidebar.text_input("AI Model", value=Config.OPENROUTER_MODEL if Config else "mistralai/mistral-7b-instruct")

if 'connector' not in st.session_state:
    st.session_state.connector = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")

# --- UNIFIED PORTFOLIO LOGIC ---
if trading_mode == "Unified Portfolio":
    st.header("🌍 Unified Portfolio Overview")

    if st.button("Fetch All Accounts"):
        with st.spinner("Connecting to all exchanges..."):
            pm = PortfolioManager()
            loop = get_or_create_event_loop()

            # 1. IBKR
            if Config and Config.IB_HOST:
                pm.add_connector(IBKRConnector(Config.IB_HOST, Config.IB_PORT, Config.IB_CLIENT_ID))

            # 2. Binance
            if Config and Config.BINANCE_API_KEY:
                pm.add_connector(CCXTConnector(
                    Config.BINANCE_API_KEY.get_secret_value(),
                    Config.BINANCE_SECRET_KEY.get_secret_value(),
                    exchange_id='binance',
                    testnet=Config.BINANCE_TESTNET
                ))

            # 3. Coinbase
            if Config and Config.COINBASE_API_KEY:
                pm.add_connector(CCXTConnector(
                    Config.COINBASE_API_KEY.get_secret_value(),
                    Config.COINBASE_SECRET_KEY.get_secret_value(),
                    exchange_id='coinbase',
                    passphrase=Config.CRYPTO_PASSPHRASE.get_secret_value() if Config.CRYPTO_PASSPHRASE else None
                ))

            # 4. Kraken
            if Config and Config.KRAKEN_API_KEY:
                pm.add_connector(CCXTConnector(
                    Config.KRAKEN_API_KEY.get_secret_value(),
                    Config.KRAKEN_SECRET_KEY.get_secret_value(),
                    exchange_id='kraken'
                ))

            try:
                loop.run_until_complete(pm.connect_all())
                summary = loop.run_until_complete(pm.get_aggregated_summary())
                positions = loop.run_until_complete(pm.get_all_positions())
                loop.run_until_complete(pm.disconnect_all())

                st.metric("Total Net Worth (USD/USDT)", f"${summary.net_liquidation:,.2f}")

                if positions:
                    st.subheader("Aggregated Positions")
                    # Convert to DataFrame
                    data = []
                    for p in positions:
                        data.append({
                            "Symbol": p.symbol,
                            "Quantity": p.quantity,
                            "Type": p.asset_type,
                            "Avg Cost": p.avg_cost
                        })
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.info("No positions found.")

            except Exception as e:
                st.error(f"Error fetching portfolio: {e}")

# --- INDIVIDUAL TRADING MODES ---
else:
    # Mode Specifics
    if trading_mode == "IBKR (Stocks)":
        st.sidebar.subheader("IBKR Settings")
        ib_host = st.sidebar.text_input("IB Host", value=Config.IB_HOST if Config else "127.0.0.1")
        ib_port = st.sidebar.number_input("IB Port", value=Config.IB_PORT if Config else 7497)
        client_id = st.sidebar.number_input("Client ID", value=Config.IB_CLIENT_ID if Config else 1)

        if st.button("Connect to IBKR"):
            try:
                connector = IBKRConnector(host=ib_host, port=ib_port, client_id=client_id)
                loop = get_or_create_event_loop()
                loop.run_until_complete(connector.connect())
                st.session_state.connector = connector
                st.session_state.mode = 'IBKR'
                st.success("Connected to IBKR")
            except Exception as e:
                st.error(f"IBKR Connection failed: {e}")

    elif trading_mode == "Crypto (Generic)": # Crypto
        st.sidebar.subheader("Crypto Settings")
        exchange_id = st.sidebar.selectbox("Exchange", ["binance", "coinbase", "kraken", "kucoin"], index=0)

        # Use Config values if available
        def_key = Config.BINANCE_API_KEY.get_secret_value() if Config and Config.BINANCE_API_KEY else ""
        def_sec = Config.BINANCE_SECRET_KEY.get_secret_value() if Config and Config.BINANCE_SECRET_KEY else ""

        bin_key = st.sidebar.text_input("API Key", value=def_key, type="password")
        bin_secret = st.sidebar.text_input("API Secret", value=def_sec, type="password")
        testnet = st.sidebar.checkbox("Testnet", value=Config.BINANCE_TESTNET if Config else False)

        if st.button("Connect to Exchange"):
            try:
                connector = CCXTConnector(api_key=bin_key, secret_key=bin_secret, exchange_id=exchange_id, testnet=testnet)
                loop = get_or_create_event_loop()
                loop.run_until_complete(connector.connect())
                st.session_state.connector = connector
                st.session_state.mode = 'CRYPTO'
                st.success(f"Connected to {exchange_id}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

    # Disconnect Logic
    if st.session_state.connector and st.session_state.connector.connected:
        if st.sidebar.button("Disconnect"):
            loop = get_or_create_event_loop()
            loop.run_until_complete(st.session_state.connector.disconnect())
            st.session_state.connector = None
            st.rerun()

    # Dashboard View (Single Connector)
    if st.session_state.connector and st.session_state.connector.connected:
        engine = st.session_state.connector

        st.header("2. Portfolio")
        if st.button("Refresh Account"):
            try:
                loop = get_or_create_event_loop()

                summary = loop.run_until_complete(engine.get_account_summary())

                col1, col2 = st.columns(2)
                col1.metric("Net Liquidation", f"{summary.net_liquidation} {summary.currency}")
                col2.metric("Total Cash", f"{summary.total_cash} {summary.currency}")

                positions = loop.run_until_complete(engine.get_positions())
                if positions:
                    st.write("Positions:")
                    # Convert list of Position objects to Dict for DataFrame
                    pos_data = [
                        {"Symbol": p.symbol, "Quantity": p.quantity, "Avg Cost": p.avg_cost}
                        for p in positions
                    ]
                    st.dataframe(pd.DataFrame(pos_data))
                else:
                    st.info("No positions.")
            except Exception as e:
                st.error(f"Error fetching account data: {e}")

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
                    loop = get_or_create_event_loop()

                    market_data = loop.run_until_complete(engine.get_market_data(symbol))

                    if market_data:
                        st.subheader(f"Market Data: {symbol}")
                        col_price, col_tech = st.columns(2)
                        with col_price:
                            st.metric("Last Price", market_data.last)
                            st.metric("Volume", market_data.volume)

                        with col_tech:
                            inds = market_data.indicators
                            st.write("**Indicators**")
                            st.write(f"SMA 20: {inds.get('SMA_20', 'N/A')}")
                            st.write(f"RSI: {inds.get('RSI', 'N/A')}")
                            st.write(f"MACD: {inds.get('MACD', 'N/A')}")

                        ai = AIWrapper(api_key, model)

                        # Prepare dict for AI
                        md_dict = {
                            'symbol': market_data.symbol,
                            'last': market_data.last,
                            'bid': market_data.bid,
                            'ask': market_data.ask,
                            'volume': market_data.volume,
                            'timestamp': market_data.timestamp,
                            **market_data.indicators
                        }

                        with st.spinner("AI Thinking..."):
                            decision = loop.run_until_complete(ai.analyze_and_decide(md_dict))

                        if decision:
                            st.subheader("AI Decision")
                            st.write(f"**Action:** {decision['decision']}")
                            st.write(f"**Reason:** {decision['args'].get('reason', 'No reason')}")
                            log(f"AI Decision: {decision['decision']}")

                            cmd = decision['decision']
                            args = decision['args']

                            if cmd in ['buy_stock', 'sell_stock']:
                                with st.spinner("Executing Order..."):
                                    action = 'BUY' if cmd == 'buy_stock' else 'SELL'
                                    res = loop.run_until_complete(engine.execute_order(
                                        args['symbol'], action, args['quantity'], 'MKT',
                                        stop_loss=args.get('stop_loss'),
                                        take_profit=args.get('take_profit')
                                    ))
                                    st.success(f"Order {res.order_id} Placed: {res.status}")
                                    log(f"{action} {args['quantity']} {args['symbol']}")
                            else:
                                st.info("Holding position.")
                    else:
                        st.error("Failed to fetch market data.")
                except Exception as e:
                     st.error(f"Error during execution: {e}")
                     log(f"Error: {e}")

    st.header("4. System Logs")
    for l in reversed(st.session_state.logs):
        st.text(l)
