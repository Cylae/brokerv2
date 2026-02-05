import logging
from config import Config

class RiskManager:
    def __init__(self, account_data_provider):
        """
        :param account_data_provider: A function or object to fetch current account values (NetLiquidation, etc.)
        """
        self.account_data_provider = account_data_provider
        self.logger = logging.getLogger(__name__)

    async def validate_trade(self, symbol, quantity, price, action, stop_loss=None):
        """
        Checks if a trade violates any risk rules.
        Returns: (True, "OK") or (False, "Reason")
        """

        # 1. Fetch Account Data
        try:
            account_data = await self.account_data_provider()
        except Exception as e:
            self.logger.error(f"Risk Check Failed: Could not fetch account data. {e}")
            return False, "Could not fetch account data"

        net_liquidation = float(account_data.get('NetLiquidation', 0))
        if net_liquidation <= 0:
            return False, "Account value is zero or negative."

        # 2. Check Daily Loss Limit (Hypothetical implementation - requires tracking daily PnL)
        # Assuming account_data has 'UnrealizedPnL' and 'RealizedPnL' combined or we track it.
        # For this MVP, we'll skip complex daily PnL tracking unless provided by IBKR directly in a simple field.
        # IBKR provides 'UnrealizedPnL' and 'RealizedPnL'.
        # daily_pnl = float(account_data.get('RealizedPnL', 0)) + float(account_data.get('UnrealizedPnL', 0))
        # max_loss_amt = net_liquidation * Config.MAX_DAILY_LOSS_PCT
        # if daily_pnl < -max_loss_amt:
        #     return False, f"Daily loss limit hit ({daily_pnl} < -{max_loss_amt})"

        # 3. Position Sizing Check
        trade_value = quantity * price
        max_position_value = net_liquidation * Config.MAX_POSITION_SIZE_PCT

        if trade_value > max_position_value:
            return False, f"Position size {trade_value} exceeds max allowed {max_position_value} (10% of equity)"

        # 4. Stop Loss Check
        if Config.REQUIRE_STOP_LOSS and stop_loss is None:
            return False, "Stop Loss is REQUIRED for safety."

        # 5. Risk Per Trade Check (Based on Stop Loss distance)
        if stop_loss:
            risk_per_share = abs(price - stop_loss)
            total_risk = risk_per_share * quantity
            max_risk_amt = net_liquidation * Config.MAX_RISK_PER_TRADE_PCT

            if total_risk > max_risk_amt:
                return False, f"Risk {total_risk:.2f} exceeds max allowed {max_risk_amt:.2f} (2% of equity)"

        return True, "Trade Approved"
