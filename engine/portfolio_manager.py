import asyncio
import logging
from typing import List, Dict
from .base_connector import BaseConnector
from .models import AccountSummary, Position

class PortfolioManager:
    def __init__(self, connectors: List[BaseConnector]):
        self.connectors = connectors
        self.logger = logging.getLogger(__name__)

    async def get_unified_account_summary(self) -> AccountSummary:
        """
        Aggregates account summaries from all connectors.
        Assumes USD or USDT as base currency and sums them up.
        """
        net_liquidation = 0.0
        total_cash = 0.0
        currency = "USD" # Default unified currency

        tasks = []
        for connector in self.connectors:
            if await connector.check_connection():
                tasks.append(connector.get_account_summary())

        if not tasks:
            return AccountSummary(0.0, 0.0, currency)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, AccountSummary):
                # Simple aggregation: Assume 1 USDT ~= 1 USD for display purposes
                # In a real system, we'd fetch FX rates.
                net_liquidation += res.net_liquidation
                total_cash += res.total_cash
            elif isinstance(res, Exception):
                self.logger.error(f"Error fetching account summary: {res}")

        return AccountSummary(
            net_liquidation=net_liquidation,
            total_cash=total_cash,
            currency=currency
        )

    async def get_unified_positions(self) -> List[Position]:
        """
        Aggregates positions from all connectors.
        """
        all_positions = []

        tasks = []
        for connector in self.connectors:
            if await connector.check_connection():
                tasks.append(connector.get_positions())

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, list):
                all_positions.extend(res)
            elif isinstance(res, Exception):
                self.logger.error(f"Error fetching positions: {res}")

        return all_positions

    async def connect_all(self):
        tasks = [connector.connect() for connector in self.connectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                self.logger.error(f"Error connecting: {res}")

    async def disconnect_all(self):
        tasks = [connector.disconnect() for connector in self.connectors]
        await asyncio.gather(*tasks, return_exceptions=True)
