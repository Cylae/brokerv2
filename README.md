# 🤖 Autonomous Multi-Model AI Trading System (Pro)

Welcome! This is a professional-grade trading system that uses Artificial Intelligence (like GPT-4 or Mistral) to analyze markets and execute trades.

**New Feature:** Now supports **Crypto (Binance)** in addition to Stocks (Interactive Brokers).

## 🚀 Quick Start (4 Steps)

### 1. Install Prerequisites
*   **Python 3.9+**
*   **For Stocks:** Interactive Brokers TWS or Gateway.
*   **For Crypto:** A Binance Account (API Key & Secret).

### 2. Setup the Code
```bash
pip install -r requirements.txt
```

### 3. Configure Your Keys
1.  Rename `.env.example` to `.env`.
2.  Add your keys:
    *   `OPENROUTER_KEY`: Required for AI.
    *   `IB_ACCOUNT`: If trading stocks.
    *   `BINANCE_API_KEY` & `SECRET`: If trading crypto.

### 4. Run It!
```bash
python easy_start.py
```
Choose **IBKR Mode** (Stocks) or **Binance Mode** (Crypto).

---

## 🛡️ Professional Features

### 1. Multi-Asset Support
*   **Stocks:** Full support via Interactive Brokers. Uses Bracket Orders for safety.
*   **Crypto:** Support for Binance Spot trading. Uses `ccxt` library for robust connectivity.

### 2. The "Senior Quant" AI Strategy
The AI acts as a Hedge Fund Manager using **Chain of Thought** reasoning.
*   **Technical Analysis:** RSI, MACD, SMA, Bollinger Bands.
*   **Risk Aware:** Calculates Stop Loss and Position Size dynamically.

### 3. Institutional Risk Management
*   **Max Risk Per Trade:** 2% of equity.
*   **Max Position Size:** 10% of equity.
*   **Mandatory Stop Loss:** Trades are rejected without one.

### 4. Production Ready
*   **Database:** Local SQLite DB stores every trade.
*   **Notifications:** Discord Webhooks for real-time alerts.
*   **Resilience:** Auto-reconnect logic and exponential backoff.
*   **Market Hours:** Sleeps when NYSE is closed (Stock Mode). Runs 24/7 (Crypto Mode).

## ⚠️ Disclaimer
**Educational Use Only.** Trading involves significant risk.
*   **Paper Trading:** Always start with IBKR Paper Trading or Binance Testnet.
*   **Crypto Spot:** Note that automated Bracket Orders (Stop Loss + Take Profit) are simulated or limited on Binance Spot. Monitor trades carefully.
