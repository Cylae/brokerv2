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

@pytest.mark.asyncio
async def test_db_init_exception():
    # Attempt to initialize with a read-only or invalid directory
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        # Pass a path that is actually a directory so it fails to connect/create a file
        db = DatabaseManager(db_path=d)
        # Should not raise but logs an error

@pytest.mark.asyncio
async def test_log_trade_exception(db):
    # Overwrite db_path to a bad path to cause sqlite exception during insert
    db.db_path = "/invalid/path/that/does/not/exist/db.sqlite"
    # Should not raise, just log error
    await db.log_trade("AAPL", "BUY", 10, 150.0, 140.0, 160.0, "Test", 123)

@pytest.mark.asyncio
async def test_get_recent_trades_exception(db):
    # Cause exception during fetch
    db.db_path = "/invalid/path/that/does/not/exist/db.sqlite"
    trades = await db.get_recent_trades()
    assert trades == []

@pytest.mark.asyncio
async def test_db_manager_close(db):
    db.close()
