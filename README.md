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
*   **Configuration:** Strict validation using `pydantic`.

---

## 🎓 Zero-to-Hero Tutorial: Your First Trade

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
*   **Stocks (Optional):** Download [TWS (Trader Workstation)](https://www.interactivebrokers.com/en/trading/tws.php). Log in with your **Paper Trading** account.
    *   Go to `File -> Global Configuration -> API -> Settings`.
    *   Check **"Enable ActiveX and Socket Clients"**.
    *   Uncheck **"Read-Only API"**.
    *   Note the Port (usually **7497** for paper).
*   **Crypto (Optional):** Go to Binance Testnet or use your real account (BE CAREFUL). Get an API Key and Secret.

### Step 3: Configure the System
1.  Rename `.env.example` to `.env`.
2.  Open `.env` and fill in your keys:
    ```env
    OPENROUTER_KEY=sk-or-v1-your-key-here

    # If trading stocks:
    IB_ACCOUNT=DU12345
    IB_PORT=7497

    # If trading crypto:
    BINANCE_API_KEY=your-api-key
    BINANCE_SECRET_KEY=your-secret-key
    BINANCE_TESTNET=True
    ```

### Step 4: Launch the Dashboard
Run the "Easy Launcher" to verify everything works.
```bash
python easy_start.py
```
1.  Select **Option 1 (Launch Dashboard)**.
2.  A web page will open.
3.  On the sidebar, select **Trading Mode** (e.g., "Crypto").
4.  Click **Connect**. You should see a green "Connected" message.

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
# Example: Trade Crypto 24/7
python main.py --mode CRYPTO --symbols BTC/USDT ETH/USDT --loop
```
The bot will now run forever, sleeping for 60 seconds between analysis cycles.

---

## 📚 Module Guide (Architecture)

### 1. Engine (`engine/`)
The heart of the system.
*   `base_connector.py`: The abstract blueprint for all exchanges.
*   `ib_connector.py`: The specialized driver for Interactive Brokers.
*   `ccxt_connector.py`: The universal driver for Crypto exchanges.
*   `risk_manager.py`: The "Gatekeeper". Validates every trade against safety rules before execution. Returns `RiskCheck` objects.
*   `market_utils.py`: Knows when markets open and close.
*   `db_manager.py`: Handles persistent storage (SQLite).
*   `notifier.py`: Sends Discord webhooks.
*   `models.py`: Unified data structures (`MarketData`, `Position`, `RiskCheck` etc.).
*   `errors.py`: Centralized exception hierarchy.

### 2. AI (`ai/`)
The brain.
*   `ai_wrapper.py`: Connects to OpenRouter using `AsyncOpenAI`. Handles Function Calling.
*   `prompt_manager.py`: Stores the "Senior Quant" persona and Chain-of-Thought prompts.

### 3. Dashboard (`dashboard/`)
The eyes.
*   `app.py`: A Streamlit web application. Supports "Unified Portfolio" view to aggregate net worth across exchanges.

---

## 🚀 Advanced Setup (Environment Variables)

Full list of supported variables in `.env`:

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
This runs ~20 tests covering connection logic, AI reasoning, risk management, and order execution mocks.
