# 🤖 Autonomous Multi-Model AI Trading System (Pro)

The ultimate "Senior Quantitative Architect" grade trading system. It combines Python, Interactive Brokers (Stocks), CCXT (Crypto), and OpenRouter (LLMs) into a unified, autonomous trading machine.

## 🌟 Key Features

*   **Universal Connectivity:**
    *   **Stocks/Options:** Interactive Brokers (IBKR) via `ib_insync`.
    *   **Crypto:** Binance, Coinbase, Kraken, etc., via `ccxt`.
*   **Unified Architecture:** A robust `BaseConnector` interface means the bot treats Apple stock and Bitcoin exactly the same.
*   **AI-Driven Decisions:** Uses GPT-4, Mistral, or Grok to analyze technical indicators and market data.
*   **Institutional Safety:**
    *   **Risk Manager:** Hard-coded limits (Max Risk 2%, Max Position 10%).
    *   **Stop Losses:** Mandatory for every trade.
    *   **Market Hours:** Respects NYSE hours for stocks, runs 24/7 for crypto.
*   **Production Ready:**
    *   **Database:** SQLite persistence for trade history.
    *   **Notifications:** Real-time Discord alerts.
    *   **Resilience:** Auto-reconnect logic with exponential backoff.

---

## 📚 Module Guide (Architecture)

### 1. Engine (`engine/`)
The heart of the system.
*   `base_connector.py`: The abstract blueprint for all exchanges.
*   `ib_connector.py`: The specialized driver for Interactive Brokers.
*   `ccxt_connector.py`: The universal driver for Crypto exchanges.
*   `risk_manager.py`: The "Gatekeeper". Validates every trade against safety rules before execution.
*   `market_utils.py`: Knows when markets open and close.
*   `db_manager.py`: Handles persistent storage (SQLite).
*   `notifier.py`: Sends Discord webhooks.
*   `models.py`: Unified data structures (`MarketData`, `Position`, etc.).

### 2. AI (`ai/`)
The brain.
*   `ai_wrapper.py`: Connects to OpenRouter using `AsyncOpenAI`. Handles Function Calling.
*   `prompt_manager.py`: Stores the "Senior Quant" persona and Chain-of-Thought prompts.

### 3. Dashboard (`dashboard/`)
The eyes.
*   `app.py`: A Streamlit web application to view portfolio status and manually trigger AI analysis.

---

## 🚀 Operational Guide

### Prerequisites
1.  **Python 3.10+**
2.  **IB Gateway / TWS:** (For Stocks) Must be running and listening on port 7497 (Paper) or 7496 (Live).
3.  **API Keys:** OpenRouter (AI) and Binance/Coinbase (Crypto).

### Setup (Environment Variables)
Create a `.env` file with these keys:

```env
# --- GENERAL ---
# Choose 'IBKR' or 'CRYPTO'
TRADING_MODE=IBKR
CRYPTO_EXCHANGE=binance

# --- AI ---
OPENROUTER_KEY=sk-or-v1-...
OPENROUTER_MODEL=mistralai/mistral-7b-instruct

# --- IBKR ---
IB_ACCOUNT=DU12345
IB_HOST=127.0.0.1
IB_PORT=7497

# --- CRYPTO ---
BINANCE_API_KEY=...
BINANCE_SECRET_KEY=...
BINANCE_TESTNET=True

# --- NOTIFICATIONS ---
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Running the System

**Option A: The Easy Launcher (Best for Noobs)**
```bash
python easy_start.py
```
*   Select **1** for Dashboard.
*   Select **2** for Auto-Trader (IBKR).
*   Select **3** for Auto-Trader (Crypto).

**Option B: The Command Line (Best for Pros)**
```bash
# Run Crypto Bot on Kraken
python main.py --mode CRYPTO --exchange kraken --symbols BTC/USD ETH/USD --loop

# Run Stock Bot on IBKR
python main.py --mode IBKR --symbols AAPL TSLA NVDA --loop
```

---

## ⚠️ Security & Risk Warning

*   **Real Money:** Trading involves significant risk. This software is provided for educational purposes only.
*   **Paper Trading:** ALWAYS start with IBKR Paper Trading or Crypto Testnets.
*   **Stop Losses:** While the bot attempts to place Stop Losses, exchange outages or volatility can prevent execution.
*   **API Keys:** Keep your `.env` file safe. Never commit it to GitHub.

---

## 🧪 Testing (The Loop)

To verify the system integrity, run the test suite:
```bash
python -m pytest
```
This runs 20+ tests covering connection logic, AI reasoning, risk management, and order execution mocks.
