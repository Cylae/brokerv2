import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from ai.ai_wrapper import AIWrapper
from engine.ccxt_connector import CCXTConnector

@pytest.mark.asyncio
async def test_ai_hallucination_detection():
    # Mock AI outputting GOOGL when asked about BTC/USDT
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Simulate a Tool Call for GOOGL
    mock_message.tool_calls = [MagicMock()]
    mock_message.tool_calls[0].function.name = "buy_stock"
    mock_message.tool_calls[0].function.arguments = json.dumps({
        "symbol": "GOOGL",
        "quantity": 10,
        "stop_loss": 100,
        "reason": "Testing"
    })

    mock_choice.message = mock_message
    mock_client.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[mock_choice]))

    # Patch the client instance created inside __init__
    with patch('ai.ai_wrapper.AsyncOpenAI', return_value=mock_client):
        ai = AIWrapper('key', 'model')
        # We need to manually assign the client because __init__ is called before we can access instance
        # Actually, simpler to patch the class that returns the client
        ai.client = mock_client

        market_data = {'symbol': 'BTC/USDT', 'last': 50000}
        decision = await ai.analyze_and_decide(market_data)

        # Should be converted to hold_position due to hallucination
        assert decision['decision'] == 'hold_position'
        assert "Hallucination Blocked" in decision['args']['reason']

@pytest.mark.asyncio
async def test_ccxt_timeout_handling():
    # Mock ccxt fetch_ticker raising Exception
    mock_exchange = MagicMock()
    mock_exchange.load_markets = AsyncMock()
    # Simulate Timeout
    mock_exchange.fetch_ticker = AsyncMock(side_effect=Exception("Request Timeout"))
    mock_exchange.fetch_ohlcv = AsyncMock(return_value=[])

    with patch('ccxt.async_support.binance', return_value=mock_exchange):
        connector = CCXTConnector('key', 'secret', 'binance')

        # Should catch exception and return None
        market_data = await connector.get_market_data('BTC/USDT')

        assert market_data is None

@pytest.mark.asyncio
async def test_ai_json_fallback():
    # Mock AI outputting raw JSON text instead of tool call
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.tool_calls = None
    mock_message.content = '```json\n{"function": {"name": "buy_stock", "arguments": {"symbol": "BTC/USDT", "quantity": 1, "stop_loss": 49000, "reason": "Fallback"}}}\n```'

    mock_choice.message = mock_message
    mock_client.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[mock_choice]))

    with patch('ai.ai_wrapper.AsyncOpenAI', return_value=mock_client):
        ai = AIWrapper('key', 'model')
        ai.client = mock_client

        market_data = {'symbol': 'BTC/USDT', 'last': 50000}
        decision = await ai.analyze_and_decide(market_data)

        assert decision['decision'] == 'buy_stock'
        assert decision['args']['reason'] == "Fallback"
