import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    IB_ACCOUNT = os.getenv("IB_ACCOUNT", "DU12345")
    IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
    IB_PORT = int(os.getenv("IB_PORT", "7497"))
    IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")

    LOG_FILE = "trading_system.log"

    # --- RISK MANAGEMENT SETTINGS ---
    MAX_RISK_PER_TRADE_PCT = 0.02  # Max 2% of account equity per trade
    MAX_DAILY_LOSS_PCT = 0.05      # Stop trading if down 5% today
    MAX_POSITION_SIZE_PCT = 0.10   # No single position > 10% of account
    REQUIRE_STOP_LOSS = True       # Reject orders without Stop Loss

    @classmethod
    def validate(cls):
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_KEY environment variable is not set.")
