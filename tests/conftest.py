import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.ib_connector import IBKRConnector
from ai.ai_wrapper import AIWrapper
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

@pytest.fixture
def mock_ib():
    ib = MagicMock()
    ib.connectAsync = AsyncMock()
    ib.disconnect = MagicMock()
    ib.isConnected = MagicMock(return_value=False)
    ib.qualifyContractsAsync = AsyncMock()
    ib.reqMktData = MagicMock()
    ib.placeOrder = MagicMock()
    ib.reqHistoricalDataAsync = AsyncMock(return_value=[])
    return ib

@pytest.fixture
def mock_ib_connector(mock_ib):
    connector = IBKRConnector()
    connector.ib = mock_ib
    return connector

@pytest.fixture
def mock_openai():
    client = MagicMock()
    client.chat.completions.create = AsyncMock()
    return client
