import pytest
import os
from engine.db_manager import DatabaseManager

TEST_DB = "test_trading.db"

@pytest.fixture
def db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    manager = DatabaseManager(TEST_DB)
    yield manager
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

@pytest.mark.asyncio
async def test_log_and_retrieve_trade(db):
    await db.log_trade(
        symbol="AAPL",
        action="BUY",
        quantity=10,
        price=150.0,
        stop_loss=145.0,
        take_profit=160.0,
        reason="Test Trade",
        order_id=12345
    )

    trades = await db.get_recent_trades()
    assert len(trades) == 1
    t = trades[0]
    assert t['symbol'] == "AAPL"
    assert t['action'] == "BUY"
    assert t['quantity'] == 10
    assert t['price'] == 150.0
    assert t['reason'] == "Test Trade"
