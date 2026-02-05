# 🤖 Autonomous Multi-Model AI Trading System

Welcome! This is a system that uses Artificial Intelligence (like GPT-4 or Mistral) to analyze the stock market and make trading decisions automatically.

It was designed to be easy to set up and use, even if you are new to coding.

## 🚀 Quick Start (4 Steps)

### 1. Install Prerequisites
You need two things installed on your computer:
*   **Python:** [Download Python here](https://www.python.org/downloads/). (Make sure to check "Add Python to PATH" during installation).
*   **Interactive Brokers TWS or Gateway:** [Download TWS here](https://www.interactivebrokers.com/en/trading/tws.php). You need an account (a **Paper Trading** account is best for testing).

### 2. Setup the Code
Open your terminal (Command Prompt or Terminal) and run these commands:

```bash
# Install the necessary libraries
pip install -r requirements.txt
```

### 3. Configure Your Keys
1.  Find the file named `.env.example`.
2.  Rename it to `.env`.
3.  Open `.env` in a text editor (Notepad, TextEdit, VS Code).
4.  **Important:** You need an **OpenRouter API Key** (allows the AI to "talk"). Get one here: [https://openrouter.ai/keys](https://openrouter.ai/keys).
5.  Paste your key into the `.env` file where it says `OPENROUTER_KEY=...`.
6.  Ensure your **IB Account ID** matches what is shown in your TWS/Gateway software.

### 4. Run It!
We made a simple launcher for you. Just run:

```bash
python easy_start.py
```

You will see a menu:
*   **Option 1 (Dashboard):** Opens a web page where you can see charts and manually ask the AI for advice.
*   **Option 2 (Auto-Trader):** Runs in the background, constantly checking stocks and trading on its own.

---

## 📚 Beginner's Guide

### What is "Paper Trading"?
**Paper Trading** means trading with fake money. Interactive Brokers gives you a simulated account (usually starting with `DU...`).
**ALWAYS** use this mode first. Do not use your real money account until you are 100% sure you know what you are doing. The AI can make mistakes!

### What is "TWS" or "IB Gateway"?
To trade with Interactive Brokers, you need their software running on your computer.
*   **TWS (Trader Workstation):** The full trading interface. Good for watching the market.
*   **IB Gateway:** A lightweight version just for connecting software like this.
*   **Note:** You must enable **"ActiveX and Socket Clients"** in the API Settings of TWS/Gateway for this program to connect.
    *   Go to: `File -> Global Configuration -> API -> Settings`.
    *   Check "Enable ActiveX and Socket Clients".
    *   Uncheck "Read-Only API".

### How does the AI work?
1.  **Fetch:** The system pulls the latest price and volume data for a stock (e.g., Apple).
2.  **Think:** It sends this data to the AI (e.g., Mistral or GPT-4).
3.  **Decide:** The AI looks at the numbers and decides to **BUY**, **SELL**, or **HOLD**.
4.  **Act:** If the AI says BUY, the system sends an order to your broker automatically.

---

## 🛠 Troubleshooting

*   **"Connection failed"**: Make sure TWS/Gateway is running and the port in your `.env` file (usually 7497) matches the port in TWS API Settings.
*   **"OPENROUTER_KEY missing"**: You didn't save your `.env` file correctly, or you didn't paste the key.
*   **"Module not found"**: You forgot to run `pip install -r requirements.txt`.

## ⚠️ Disclaimer
**This software is for educational purposes only.**
Trading involves risk. The AI can hallucinate (make up facts). Never trade money you cannot afford to lose.
