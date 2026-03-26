import pytest
import inspect
from engine.base_connector import BaseConnector
from engine.models import AccountSummary

def test_base_connector_is_abstract():
    # Attempting to instantiate the abstract class directly should fail
    with pytest.raises(TypeError):
        BaseConnector()

@pytest.mark.asyncio
async def test_base_connector_methods_pass():
    # To hit the `pass` statements in abstract methods for coverage,
    # we need to call the functions directly on the class or bypass the ABC metaclass.

    # We can call the unbound methods directly passing None as self
    assert await BaseConnector.connect(None) is None
    assert await BaseConnector.disconnect(None) is None
    assert await BaseConnector.check_connection(None) is None
    assert await BaseConnector.get_market_data(None, "AAPL") is None
    assert await BaseConnector.execute_order(None, "AAPL", "BUY", 10) is None
    assert await BaseConnector.get_account_summary(None) is None
    assert await BaseConnector.get_positions(None) is None
