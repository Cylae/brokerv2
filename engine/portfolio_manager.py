import asyncio
from typing import List
from .base_connector import BaseConnector
from .models import AccountSummary, Position

class PortfolioManager:
    def __init__(self):
        self.connectors: List[BaseConnector] = []

    def add_connector(self, connector: BaseConnector):
        self.connectors.append(connector)

    async def connect_all(self):
        tasks = [c.connect() for c in self.connectors]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def disconnect_all(self):
        tasks = [c.disconnect() for c in self.connectors]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_aggregated_summary(self) -> AccountSummary:
        total_net_liq = 0.0
        total_cash = 0.0
        # Default currency USD, but we might mix USDT. We'll just sum them 1:1 for simplicity.
        # For this version, we assume 1 USD ~= 1 USDT

        tasks = [c.get_account_summary() for c in self.connectors]
        if not tasks:
            return AccountSummary(0.0, 0.0, "USD")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, AccountSummary):
                total_net_liq += res.net_liquidation
                total_cash += res.total_cash

        return AccountSummary(
            net_liquidation=total_net_liq,
            total_cash=total_cash,
            currency="USD/USDT"
        )

    async def get_all_positions(self) -> List[Position]:
        tasks = [c.get_positions() for c in self.connectors]
        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_positions = []

        for res in results:
            if isinstance(res, list):
                all_positions.extend(res)

        return all_positions
