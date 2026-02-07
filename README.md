# 🤖 Autonomous Multi-Model AI Trading System (Pro)

The ultimate "Senior Quantitative Architect" grade trading system. It combines Python, Interactive Brokers (Stocks), CCXT (Crypto), and OpenRouter (LLMs) into a unified, autonomous trading machine.

## 🌟 Key Features

*   **Universal Connectivity:**
    *   **Stocks/Options:** Interactive Brokers (IBKR) via `ib_insync`.
    *   **Crypto:** Binance, Coinbase, Kraken, etc., via `ccxt`. Supports API Keys, Secrets, and Passphrases.
*   **Unified Architecture:**
    *   `BaseConnector`: Unified interface for all assets.
    *   `PortfolioManager`: Aggregates positions and net worth from all connected exchanges (IBKR + Crypto) into a single "Unified Portfolio" view.
*   **AI-Driven Decisions:** Uses GPT-4, Mistral, Gemini, or Grok to analyze technical indicators and market data via OpenRouter.
    *   **Robust Tool Use:** Forces structured JSON output (Buy/Sell/Hold).
    *   **Hallucination Protection:** Verifies AI output against requested symbols.
*   **Institutional Safety:**
    *   **Risk Manager:** Hard-coded limits (Max Risk 2%, Max Position 10%).
    *   **Stop Losses:** Mandatory for every trade.
    *   **Market Hours:** Respects NYSE hours for stocks, runs 24/7 for crypto.
*   **Production Ready:**
    *   **Database:** SQLite persistence for trade history.
    *   **Notifications:** Real-time Discord alerts.
    *   **Resilience:** Auto-reconnect logic and API timeout handling.
*   **Security:**
    *   **Web Dashboard Auth:** Protect your interface with a username/password.
    *   **Strict Validation:** Configuration validated via `pydantic`.

---

## 🎓 Zero-to-Hero Tutorial

Follow this guide to go from "Empty Folder" to "AI Trading" safely.

### Step 1: Install & Setup
1.  **Clone the Repo:** Download this code to your machine.
2.  **Install Python:** Ensure you have Python 3.10+ installed.
3.  **Install Libraries:**
    ```bash
    pip install -r requirements.txt
    ```

### Step 2: Get Your Keys (Paper Trading ONLY!)
*   **AI:** Go to [OpenRouter.ai](https://openrouter.ai), create an account, and generate an API Key.
    *   *Supported Models:* `mistralai/mistral-7b-instruct`, `google/gemini-2.0-flash-exp:free`, `openai/gpt-4-turbo`.
*   **Stocks (Optional):** Download [TWS (Trader Workstation)](https://www.interactivebrokers.com/en/trading/tws.php). Log in with your **Paper Trading** account.
    *   Go to `File -> Global Configuration -> API -> Settings`.
    *   Check **"Enable ActiveX and Socket Clients"**.
    *   Uncheck **"Read-Only API"**.
    *   Note the Port (usually **7497** for paper).
*   **Crypto (Optional):** Go to Binance Testnet, Coinbase Advanced Trade, or Kraken. Get an API Key, Secret, and Passphrase (if required).

### Step 3: Configure the System
1.  Rename `.env.example` to `.env`.
2.  Open `.env` and fill in your keys:
    ```env
    OPENROUTER_KEY=sk-or-v1-your-key-here
    OPENROUTER_MODEL=mistralai/mistral-7b-instruct

    # Dashboard Security
    DASHBOARD_USERNAME=admin
    DASHBOARD_PASSWORD=securepassword123

    # If trading stocks:
    IB_ACCOUNT=DU12345
    IB_HOST=127.0.0.1
    IB_PORT=7497

    # If trading crypto:
    CRYPTO_EXCHANGE=binance  # or coinbase, kraken, kucoin
    CRYPTO_API_KEY=your-api-key
    CRYPTO_SECRET_KEY=your-secret-key
    CRYPTO_PASSPHRASE=your-passphrase # Optional (for Coinbase/KuCoin)
    BINANCE_TESTNET=True # Set to False for real trading
    ```

### Step 4: Launch the Dashboard
Run the "Easy Launcher" to verify everything works.
```bash
python easy_start.py
```
1.  Select **Option 1 (Launch Dashboard)**.
2.  A web page will open (usually `http://localhost:8501`).
3.  **Login** with the username/password you set in Step 3.
4.  On the sidebar, select **Trading Mode** (e.g., "Crypto (Generic)" or "Unified Portfolio").
5.  Click **Connect**. You should see a green "Connected" message.

### Step 5: Execute an AI Trade (Manual Trigger)
1.  In the Dashboard, enter a symbol (e.g., `BTC/USDT` or `AAPL`).
2.  Click **Analyze & Execute**.
3.  **Watch the Logs:**
    *   The system fetches data (Price, RSI, MACD).
    *   It sends this data to the AI.
    *   The AI "thinks" (e.g., "RSI is 30, Oversold. Trend is Up. Buy.").
    *   The **Risk Manager** checks the trade (Is position < 10%? Is Stop Loss set?).
    *   If approved, the order is placed on the exchange!

### Step 6: Go Fully Autonomous
Once you trust the system, run it in a loop from the command line:
```bash
# Example: Trade Crypto 24/7 on Coinbase
python main.py --mode CRYPTO --exchange coinbase --symbols BTC/USD ETH/USD --loop
```
The bot will now run forever, sleeping for 60 seconds between analysis cycles.

---

## 🏗 Architecture Overview

The system follows a modular "Engine-AI-Dashboard" architecture.

### 1. Engine (`engine/`)
The core trading logic and connectivity layer.
*   **Connectors:**
    *   `base_connector.py`: Abstract base class defining the standard interface (`get_market_data`, `execute_order`).
    *   `ib_connector.py`: Implementation for Interactive Brokers using `ib_insync`.
    *   `ccxt_connector.py`: Implementation for Crypto using `ccxt`. Supports generic exchanges and passphrase auth.
*   **Portfolio Manager:**
    *   `portfolio_manager.py`: Aggregates data from multiple connectors to provide a "Unified Portfolio" view (Total Net Worth, All Positions).
*   **Risk & Safety:**
    *   `risk_manager.py`: The "Gatekeeper". Validates every trade against safety rules.
    *   `models.py`: Unified data classes (`MarketData`, `TradeResult`, `Position`, `AccountSummary`, `RiskCheck`).
    *   `errors.py`: Centralized exception hierarchy.
*   **Utilities:**
    *   `market_utils.py`: Market hours logic.
    *   `db_manager.py`: SQLite trade logging.
    *   `notifier.py`: Discord notifications.

### 2. AI (`ai/`)
The intelligence layer.
*   `ai_wrapper.py`: Handles communication with OpenRouter/LLMs.
    *   **Smart Fallback:** If the LLM fails to call a tool, it attempts to parse JSON from the text response.
    *   **Hallucination Check:** Ensures the LLM is trading the symbol we asked for.
*   `prompt_manager.py`: Manages the system prompts and "Senior Quant" persona.

### 3. Dashboard (`dashboard/`)
The visualization layer.
*   `app.py`: Streamlit application. Connects to `PortfolioManager` to display real-time status and controls.

---

## 🐧 Linux Server Deployment Guide (Pro)

To run this bot on a headless Linux VPS (DigitalOcean, AWS, Linode):

### 1. Run as a Background Service (systemd)
Create a service file to keep the bot running automatically.

`sudo nano /etc/systemd/system/trading-bot.service`

```ini
[Unit]
Description=AI Trading Bot
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/trading-system
ExecStart=/usr/bin/python3 main.py --mode CRYPTO --exchange binance --loop
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable it: `sudo systemctl enable trading-bot && sudo systemctl start trading-bot`

### 2. Secure the Dashboard (Automated SSL)
We have provided a script to automatically set up Nginx and LetsEncrypt SSL.

1.  Make sure your domain (e.g., `bot.yourdomain.com`) points to your server's IP.
2.  Run the setup script as root:
    ```bash
    sudo ./scripts/setup_ssl.sh bot.yourdomain.com
    ```
3.  The script will install Nginx, configure a reverse proxy to Streamlit (Port 8501), and request an SSL certificate.

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
This runs ~30 tests covering:
*   **Stability:** API Timeout resilience and AI Hallucination protection.
*   **Logic:** Risk management rules, market hours, and trade execution mocks.
*   **Connectivity:** `ccxt` and `ib_insync` integration checks.
