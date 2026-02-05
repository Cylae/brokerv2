# Autonomous Multi-Model AI Trading System

A Python-based trading architecture that connects to Interactive Brokers (IBKR) via a Gateway, uses OpenRouter to access various LLMs (Grok, GPT-4, Claude, Mistral), and executes trades based on AI analysis.

## Prerequisites

*   **Python 3.9+**
*   **Interactive Brokers Account** (Paper Trading recommended)
*   **IB Gateway or TWS** installed and running.
*   **OpenRouter API Key**

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repo_url>
    cd trading_system
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    Create a `.env` file or export environment variables:
    ```bash
    export IB_ACCOUNT="DU12345"       # Your IBKR Account ID
    export IB_HOST="127.0.0.1"        # IB Gateway Host
    export IB_PORT="7497"             # 7497 for Paper, 7496 for Live
    export IB_CLIENT_ID="1"
    export OPENROUTER_KEY="sk-..."    # Your OpenRouter API Key
    export OPENROUTER_MODEL="mistralai/mistral-7b-instruct"
    ```

4.  **IB Gateway / TWS Settings:**
    *   Enable **ActiveX and Socket Clients**.
    *   Disable **Read-Only API** (if you want to execute trades).
    *   Ensure the port matches `IB_PORT` (default 7497 for paper).

## Usage

### Dashboard Mode (Streamlit)
To launch the interactive dashboard:
```bash
streamlit run dashboard/app.py
```

### Autonomous Mode (CLI)
To run the system in a loop:
```bash
python main.py --loop --symbols AAPL TSLA NVDA
```

## Architecture

*   **Engine:** `ib_insync` based connector for IBKR.
*   **AI:** OpenRouter wrapper supporting Tool Use/Function Calling.
*   **Dashboard:** Streamlit interface for real-time monitoring.

## ⚠️ Security & Risk Warning

*   **Real Money Trading:** This software is for **educational purposes only**. Trading stocks, options, and cryptocurrencies involves significant risk and can result in the loss of your capital.
*   **Paper Trading:** Always use a **Paper Trading (Simulated)** account for testing. Do not run this with real money unless you fully understand the code and risks.
*   **API Keys:** Never share your API keys or commit them to version control.
*   **Hallucinations:** AI models can "hallucinate" or make mistakes. Do not rely solely on AI for financial decisions.

## License

MIT
