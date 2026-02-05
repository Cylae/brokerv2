import pytest
from unittest.mock import MagicMock
import json

def test_ai_wrapper_decision_buy(mock_openai):
    from ai.ai_wrapper import AIWrapper
    ai = AIWrapper('fake_key', 'fake_model')
    ai.client = mock_openai

    # Mock response
    mock_message = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = 'buy_stock'
    mock_tool_call.function.arguments = json.dumps({
        "symbol": "AAPL",
        "quantity": 10,
        "reason": "Bullish signal"
    })
    mock_message.tool_calls = [mock_tool_call]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    mock_openai.chat.completions.create.return_value = mock_response

    market_data = {
        'symbol': 'AAPL',
        'last': 150,
        'bid': 149,
        'ask': 151,
        'volume': 1000,
        'close': 148,
        'timestamp': '2023-01-01'
    }

    decision = ai.analyze_and_decide(market_data)

    assert decision['decision'] == 'buy_stock'
    assert decision['args']['symbol'] == 'AAPL'
    assert decision['args']['quantity'] == 10

def test_ai_wrapper_no_tool_usage(mock_openai):
    from ai.ai_wrapper import AIWrapper
    ai = AIWrapper('fake_key', 'fake_model')
    ai.client = mock_openai

    # Mock response with no tool calls but text content
    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "I think we should hold."

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]

    mock_openai.chat.completions.create.return_value = mock_response

    market_data = {
        'symbol': 'AAPL',
        'last': 150,
        'bid': 149,
        'ask': 151,
        'volume': 1000,
        'close': 148,
        'timestamp': '2023-01-01'
    }

    decision = ai.analyze_and_decide(market_data)

    # Should default to hold
    assert decision['decision'] == 'hold_position'
    assert decision['args']['symbol'] == 'AAPL'
