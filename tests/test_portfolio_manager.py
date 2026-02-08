import pytest
from unittest.mock import AsyncMock, MagicMock
from engine.portfolio_manager import PortfolioManager
from engine.models import AccountSummary, Position

@pytest.mark.asyncio
async def test_aggregation():
    pm = PortfolioManager()

    # Mock Connector 1
    c1 = MagicMock()
    c1.connect = AsyncMock()
    c1.get_account_summary = AsyncMock(return_value=AccountSummary(net_liquidation=1000.0, total_cash=100.0, currency="USD"))
    c1.get_positions = AsyncMock(return_value=[Position("AAPL", 10, asset_type="STOCK")])

    # Mock Connector 2
    c2 = MagicMock()
    c2.connect = AsyncMock()
    c2.get_account_summary = AsyncMock(return_value=AccountSummary(net_liquidation=500.0, total_cash=50.0, currency="USDT"))
    c2.get_positions = AsyncMock(return_value=[Position("BTC/USDT", 0.1, asset_type="CRYPTO")])

    pm.add_connector(c1)
    pm.add_connector(c2)

    await pm.connect_all()

    summary = await pm.get_aggregated_summary()
    assert summary.net_liquidation == 1500.0
    assert summary.total_cash == 150.0

    positions = await pm.get_all_positions()
    assert len(positions) == 2
    assert positions[0].symbol == "AAPL"
    assert positions[1].symbol == "BTC/USDT"
