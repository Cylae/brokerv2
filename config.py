import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # GENERAL
    LOG_FILE = "trading_system.log"
    TRADING_MODE = os.getenv("TRADING_MODE", "IBKR").upper() # 'IBKR' or 'BINANCE'

    # IBKR
    IB_ACCOUNT = os.getenv("IB_ACCOUNT", "DU12345")
    IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
    IB_PORT = int(os.getenv("IB_PORT", "7497"))
    IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))

    # BINANCE
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
    BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "False").lower() == "true"

    # AI
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")

    # RISK
    MAX_RISK_PER_TRADE_PCT = 0.02
    MAX_DAILY_LOSS_PCT = 0.05
    MAX_POSITION_SIZE_PCT = 0.10
    REQUIRE_STOP_LOSS = True

    # NOTIFICATIONS
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

    @classmethod
    def validate(cls):
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_KEY environment variable is not set.")

        if cls.TRADING_MODE == 'BINANCE' and not cls.BINANCE_API_KEY:
             raise ValueError("BINANCE_API_KEY required for Binance mode.")
