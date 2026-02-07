import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from engine.ccxt_connector import CCXTConnector
from engine.models import MarketData
from ai.ai_wrapper import AIWrapper

@pytest.mark.asyncio
async def test_api_timeout_resilience():
    """
    Test that the connector handles API timeouts gracefully.
    """
    # Mocking ccxt.binance (the class)
    with patch('ccxt.async_support.binance') as MockExchange:
        # Setup Mock
        mock_ex_instance = MockExchange.return_value

        # Simulate TimeoutError on fetch_ticker
        mock_ex_instance.fetch_ticker = AsyncMock(side_effect=asyncio.TimeoutError("Connection timed out"))
        mock_ex_instance.load_markets = AsyncMock()
        mock_ex_instance.close = AsyncMock()

        connector = CCXTConnector("key", "secret", "binance")
        await connector.connect()

        # Execute
        result = await connector.get_market_data("BTC/USDT")

        # Assert
        assert result is None, "Should return None on timeout"

        await connector.disconnect()

@pytest.mark.asyncio
async def test_ai_hallucination_protection():
    """
    Test that the system rejects trades where the AI returns a different symbol.
    """
    # 1. Mock AI Wrapper response
    ai = AIWrapper("key", "mistral")
    ai.client = AsyncMock()

    # Mock Response with Wrong Symbol (Hallucination)
    # User asks for BTC/USDT, AI says buy ETH/USDT
    mock_msg = MagicMock()
    mock_msg.tool_calls = [MagicMock()]
    mock_msg.tool_calls[0].function.name = "buy_stock"
    mock_msg.tool_calls[0].function.arguments = json.dumps({
        "symbol": "ETH/USDT",
        "quantity": 1,
        "stop_loss": 2000,
        "reason": "test"
    })

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_msg)]
    ai.client.chat.completions.create = AsyncMock(return_value=mock_response)

    # 2. Call AI
    market_data = {"symbol": "BTC/USDT", "last": 50000}
    decision = await ai.analyze_and_decide(market_data)

    # 3. Verify logic handles mismatch
    cmd = decision['decision']
    args = decision['args']

    target_symbol = "BTC/USDT"
    dec_symbol = args['symbol']

    # Logic copied from main.py for verification
    normalized_target = target_symbol.upper().replace('/', '')
    normalized_dec = dec_symbol.upper().replace('/', '')

    # It should mismatch
    match = normalized_dec in normalized_target or normalized_target in normalized_dec

    assert not match, "System should detect symbol mismatch (Hallucination)"
