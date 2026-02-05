import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.ib_connector import IBConnector
from engine.trading_engine import TradingEngine
from ai.ai_wrapper import AIWrapper

@pytest.fixture
def mock_ib():
    ib = MagicMock()
    ib.connectAsync = AsyncMock()
    ib.disconnect = MagicMock()
    ib.isConnected = MagicMock(return_value=False)
    ib.qualifyContractsAsync = AsyncMock()
    ib.reqMktData = MagicMock()
    ib.placeOrder = MagicMock()
    return ib

@pytest.fixture
def mock_ib_connector(mock_ib):
    connector = IBConnector()
    connector.ib = mock_ib
    return connector

@pytest.fixture
def mock_openai():
    client = MagicMock()
    client.chat.completions.create = MagicMock()
    return client
