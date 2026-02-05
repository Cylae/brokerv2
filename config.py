from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Optional, Literal

class Settings(BaseSettings):
    # GENERAL
    LOG_FILE: str = "trading_system.log"
    TRADING_MODE: Literal['IBKR', 'CRYPTO', 'BINANCE'] = "IBKR"
    CRYPTO_EXCHANGE: str = "binance"

    # DASHBOARD SECURITY
    DASHBOARD_USERNAME: Optional[str] = Field(default=None, description="Username for Web Dashboard")
    DASHBOARD_PASSWORD: Optional[SecretStr] = Field(default=None, description="Password for Web Dashboard")

    # IBKR
    IB_ACCOUNT: str = Field(default="DU12345", description="IBKR Account ID")
    IB_HOST: str = "127.0.0.1"
    IB_PORT: int = 7497
    IB_CLIENT_ID: int = 1

    # BINANCE / CRYPTO
    BINANCE_API_KEY: Optional[SecretStr] = None
    BINANCE_SECRET_KEY: Optional[SecretStr] = None
    BINANCE_TESTNET: bool = False

    # AI
    OPENROUTER_KEY: SecretStr
    OPENROUTER_MODEL: str = "mistralai/mistral-7b-instruct"

    # RISK
    MAX_RISK_PER_TRADE_PCT: float = 0.02
    MAX_DAILY_LOSS_PCT: float = 0.05
    MAX_POSITION_SIZE_PCT: float = 0.10
    REQUIRE_STOP_LOSS: bool = True

    # NOTIFICATIONS
    DISCORD_WEBHOOK_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore' # Ignore extra fields in .env

# Global Instance
try:
    Config = Settings()
except Exception as e:
    print(f"Configuration Error: {e}")
    # Fallback or Exit handled by main
    Config = None
