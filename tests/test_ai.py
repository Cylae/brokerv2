import pytest
from unittest.mock import MagicMock, AsyncMock
import json

@pytest.mark.asyncio
async def test_ai_wrapper_decision_buy(mock_openai):
    from ai.ai_wrapper import AIWrapper
    ai = AIWrapper('fake_key', 'fake_model')
    ai.client = mock_openai # mock_openai is the client object

    # Mock response
    mock_message = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = 'buy_stock'
    mock_tool_call.function.arguments = json.dumps({
        "symbol": "AAPL",
        "quantity": 10,
        "stop_loss": 145,
        "reason": "Bullish"
    })
    mock_message.tool_calls = [mock_tool_call]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    # Mock Async Call
    # client.chat.completions.create is now an async method (or returns an awaitable)
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    market_data = {'symbol': 'AAPL', 'last': 150, 'bid': 149, 'ask': 151, 'volume': 1000, 'timestamp': 'now'}

    decision = await ai.analyze_and_decide(market_data)

    assert decision['decision'] == 'buy_stock'
    assert decision['args']['symbol'] == 'AAPL'

@pytest.mark.asyncio
async def test_ai_wrapper_no_tool_usage(mock_openai):
    from ai.ai_wrapper import AIWrapper
    ai = AIWrapper('fake_key', 'fake_model')

    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "Hold"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    ai.client = mock_openai

    market_data = {'symbol': 'AAPL', 'last': 150, 'bid': 149, 'ask': 151, 'volume': 1000, 'timestamp': 'now'}

    decision = await ai.analyze_and_decide(market_data)

    assert decision['decision'] == 'hold_position'

@pytest.mark.asyncio
async def test_ai_wrapper_exception(mock_openai):
    from ai.ai_wrapper import AIWrapper
    ai = AIWrapper('fake_key', 'fake_model')
    ai.client = mock_openai

    mock_openai.chat.completions.create.side_effect = Exception("API error")

    market_data = {'symbol': 'AAPL'}

    decision = await ai.analyze_and_decide(market_data)

    assert decision is None
