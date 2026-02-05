import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    IB_ACCOUNT = os.getenv("IB_ACCOUNT", "DU12345")  # Default to a dummy paper account
    IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
    IB_PORT = int(os.getenv("IB_PORT", "7497")) # 7497 is paper trading, 7496 is live
    IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct") # Default model

    LOG_FILE = "trading_system.log"

    @classmethod
    def validate(cls):
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_KEY environment variable is not set.")
