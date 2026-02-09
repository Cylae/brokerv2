# 🤖 Autonomous Multi-Model AI Trading System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Status](https://img.shields.io/badge/status-active-green)

A professional-grade, autonomous trading system connecting **Interactive Brokers (IBKR)** and **Multiple Crypto Exchanges (Binance, Coinbase, Kraken)** with state-of-the-art LLMs (GPT-4, Mistral, Gemini) via OpenRouter.

---

## 🚀 Zero-to-Hero Tutorial

### Step 1: Prerequisites
1.  **Python 3.11+**: Ensure Python is installed.
2.  **IBKR Gateway / TWS**: For stock trading, you need IBKR software running.
    -   Enable "Enable ActiveX and Socket Clients".
    -   Port: `7497` (Paper) or `7496` (Live).
3.  **Crypto API Keys**: Get API Key & Secret from your exchange (Binance, Coinbase, etc.).

### Step 2: Installation
```bash
git clone <repository_url>
cd trading-system
pip install -r requirements.txt
```

### Step 3: Configuration
Create a `.env` file in the root directory (copy `.env.example` if available) and configure your keys.

**Required Environment Variables:**
```ini
# --- AI Configuration ---
OPENROUTER_KEY=sk-or-v1-YOUR-KEY...
OPENROUTER_MODEL=mistralai/mistral-7b-instruct

# --- Dashboard Security ---
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=supersecurepassword

# --- IBKR (Stocks) ---
IB_ACCOUNT=DU12345
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1

# --- Crypto Exchanges ---
# Binance
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret

# Coinbase Advanced Trade
COINBASE_API_KEY=your_coinbase_key
COINBASE_SECRET_KEY=your_coinbase_secret

# Kraken
KRAKEN_API_KEY=your_kraken_key
KRAKEN_SECRET_KEY=your_kraken_secret

# Generic (Other)
CRYPTO_API_KEY=...
CRYPTO_SECRET_KEY=...
CRYPTO_PASSPHRASE=... # If required (e.g. KuCoin, Coinbase Pro)
```

### Step 4: Run the System
You have two modes: **Headless Loop** (CLI) or **Dashboard** (UI).

**Option A: Streamlit Dashboard (Recommended)**
```bash
streamlit run dashboard/app.py
```
-   Open `http://localhost:8501`.
-   Login with your configured credentials.
-   Select "Unified Portfolio" to view all assets.
-   Select "Crypto (Generic)" or "IBKR" to execute trades.

**Option B: Headless CLI**
```bash
# Trade Crypto on Binance
python main.py --mode CRYPTO --exchange binance --symbols BTC/USDT ETH/USDT --loop

# Trade Stocks on IBKR
python main.py --mode IBKR --symbols AAPL TSLA --loop
```

---

## 🏗 Architecture Overview

The system follows a modular **Strategy Pattern** architecture:

1.  **Data Layer (`engine/`)**:
    -   `IBKRConnector`: Uses `ib_insync` for async communication with TWS/Gateway.
    -   `CCXTConnector`: Uses `ccxt` to unify 100+ crypto exchanges.
    -   `PortfolioManager`: Aggregates data from all active connectors into a single view.
2.  **Analysis Layer (`ai/`)**:
    -   `AIWrapper`: Standardizes communication with OpenRouter.
    -   **Tool Use**: LLMs are forced to use structured tools (`buy_stock`, `sell_stock`, `hold_position`) to prevent hallucinations.
3.  **Risk Layer (`engine/risk_manager.py`)**:
    -   Validates every trade against `MAX_RISK_PER_TRADE_PCT` and `MAX_DAILY_LOSS_PCT`.
4.  **Presentation Layer (`dashboard/`)**:
    -   Streamlit-based UI for real-time monitoring and manual intervention.

---

## 📂 Module Guide

| File | Description |
|------|-------------|
| `main.py` | CLI Entry point for the autonomous loop. |
| `config.py` | Pydantic-based configuration and validation. |
| `dashboard/app.py` | The web interface. Connects to `PortfolioManager`. |
| `engine/base_connector.py` | Abstract Interface for all exchanges. |
| `engine/ib_connector.py` | IBKR implementation. |
| `engine/ccxt_connector.py` | Unified Crypto implementation (Binance, Coinbase, Kraken, etc.). |
| `engine/portfolio_manager.py`| Aggregates accounts and positions. |
| `engine/risk_manager.py` | Safety checks (Stop Loss, Position Sizing). |
| `ai/ai_wrapper.py` | Handles LLM prompting and JSON parsing. |

---

## ⚠️ Security & Risk Warning

*   **Paper Trading First**: ALWAYS test on Paper Trading (IBKR) or Testnets (Binance) before using real money.
*   **API Keys**: Never commit your `.env` file. It is in `.gitignore` by default.
*   **Stop Losses**: The system attempts to place Stop Loss orders immediately after entry. However, exchange outages or API failures can prevent this. **Monitor your positions.**
*   **AI Hallucinations**: While we use "Tool Calling" to minimize errors, LLMs can still behave unpredictably. The `RiskManager` is the final gatekeeper, but it is not infallible.

---

## 🧪 Testing

Run the full test suite to verify system integrity:
```bash
pytest tests/
```
Tests cover:
-   API Connectivity (Mocked)
-   Portfolio Aggregation
-   AI Decision Parsing
-   Stop Loss Logic

---

**Maintained by**: Senior Quantitative Architect
**Last Update**: 2026-02-08
