import pytest
from unittest.mock import MagicMock, AsyncMock
import json

@pytest.mark.asyncio
async def test_ai_wrapper_gemini_model_name(mock_openai):
    from ai.ai_wrapper import AIWrapper

    # Use a Gemini model name
    ai = AIWrapper('fake_key', 'google/gemini-2.0-flash-exp:free')
    ai.client = mock_openai

    # Mock valid tool response
    mock_message = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = 'buy_stock'
    mock_tool_call.function.arguments = json.dumps({
        "symbol": "BTC/USDT",
        "quantity": 1,
        "stop_loss": 40000,
        "reason": "Gemini says buy"
    })
    mock_message.tool_calls = [mock_tool_call]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    decision = await ai.analyze_and_decide({'symbol': 'BTC/USDT'})

    assert decision['decision'] == 'buy_stock'
    assert ai.model == 'google/gemini-2.0-flash-exp:free'
