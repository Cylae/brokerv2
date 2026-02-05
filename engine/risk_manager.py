import asyncio
import logging
import time
from config import Config
from .models import RiskCheck

class RiskManager:
    def __init__(self, account_data_provider):
        """
        :param account_data_provider: A function or object to fetch current account values (NetLiquidation, etc.)
        """
        self.account_data_provider = account_data_provider
        self.logger = logging.getLogger(__name__)

        # Caching
        self._lock = asyncio.Lock()
        self._last_account_data = None
        self._last_fetch_time = 0
        self._cache_ttl = 60  # seconds

    async def _get_account_data(self):
        """Fetches account data with caching logic."""
        current_time = time.time()

        # Fast path: check cache first
        if self._last_account_data and (current_time - self._last_fetch_time < self._cache_ttl):
            return self._last_account_data

        async with self._lock:
            # Double-check inside lock
            current_time = time.time()
            if self._last_account_data and (current_time - self._last_fetch_time < self._cache_ttl):
                return self._last_account_data

            data = await self.account_data_provider()
            self._last_account_data = data
            self._last_fetch_time = time.time()
            return data

    async def validate_trade(self, symbol, quantity, price, action, stop_loss=None) -> RiskCheck:
        """
        Checks if a trade violates any risk rules.
        Returns: RiskCheck object
        """

        # 1. Fetch Account Data
        try:
            account_data = await self._get_account_data()
            # Handle if provider returns dict or AccountSummary object
            if hasattr(account_data, 'net_liquidation'):
                net_liquidation = account_data.net_liquidation
            else:
                net_liquidation = float(account_data.get('NetLiquidation', 0))
        except Exception as e:
            self.logger.error(f"Risk Check Failed: Could not fetch account data. {e}")
            return RiskCheck(False, "Could not fetch account data")

        if net_liquidation <= 0:
            return RiskCheck(False, "Account value is zero or negative.")

        # 2. Position Sizing Check
        trade_value = quantity * price
        max_position_value = net_liquidation * Config.MAX_POSITION_SIZE_PCT

        if trade_value > max_position_value:
            return RiskCheck(False, f"Position size {trade_value:.2f} exceeds max allowed {max_position_value:.2f} (10% of equity)")

        # 3. Stop Loss Check
        if Config.REQUIRE_STOP_LOSS and stop_loss is None:
            return RiskCheck(False, "Stop Loss is REQUIRED for safety.")

        # 4. Risk Per Trade Check (Based on Stop Loss distance)
        if stop_loss:
            # For BUY, risk is Price - Stop. For SELL, Stop - Price.
            risk_per_share = abs(price - stop_loss)
            total_risk = risk_per_share * quantity
            max_risk_amt = net_liquidation * Config.MAX_RISK_PER_TRADE_PCT

            if total_risk > max_risk_amt:
                return RiskCheck(False, f"Risk {total_risk:.2f} exceeds max allowed {max_risk_amt:.2f} (2% of equity)")

        return RiskCheck(True, "Trade Approved")
