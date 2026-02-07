from openai import AsyncOpenAI
import json
import logging
from .prompt_manager import PromptManager

class AIWrapper:
    def __init__(self, api_key, model):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def analyze_and_decide(self, market_data):
        """
        Sends market data to the AI and returns the decision asynchronously.
        """
        system_prompt = PromptManager.get_system_prompt()
        user_prompt = PromptManager.format_market_data(market_data)

        # Tool Definitions
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "buy_stock",
                    "description": "Place a buy order",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Ticker symbol"},
                            "quantity": {"type": "integer", "description": "Quantity"},
                            "stop_loss": {"type": "number", "description": "Stop Loss Price"},
                            "take_profit": {"type": "number", "description": "Take Profit Price"},
                            "reason": {"type": "string", "description": "Reason"}
                        },
                        "required": ["symbol", "quantity", "stop_loss", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sell_stock",
                    "description": "Place a sell order",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Ticker symbol"},
                            "quantity": {"type": "integer", "description": "Quantity"},
                             "stop_loss": {"type": "number", "description": "Stop Loss Price"},
                            "reason": {"type": "string", "description": "Reason"}
                        },
                        "required": ["symbol", "quantity", "stop_loss", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "hold_position",
                    "description": "Hold current position",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Ticker symbol"},
                            "reason": {"type": "string", "description": "Reason"}
                        },
                        "required": ["symbol", "reason"]
                    }
                }
            }
        ]

        try:
            # Gemini Compatibility Check:
            # Some models via OpenRouter (like Gemini) might behave better with explicit prompting
            # if tool_choice='auto' isn't fully supported or optimized.
            # However, OpenRouter claims OpenAI compatibility.
            # We'll stick to standard OpenAI format.

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                return {
                    "decision": function_name,
                    "args": arguments,
                    "raw_response": message
                }
            else:
                self.logger.warning(f"AI ({self.model}) did not use a tool. Content: {message.content}")

                # Fallback: Try to parse JSON from text
                fallback_data = self._parse_fallback_json(message.content)
                if fallback_data:
                    # Heuristic: Check for explicit 'action' or 'decision' field
                    action = fallback_data.get('decision') or fallback_data.get('action')
                    if action:
                        if 'buy' in action.lower(): fn = 'buy_stock'
                        elif 'sell' in action.lower(): fn = 'sell_stock'
                        else: fn = 'hold_position'
                        return {
                            "decision": fn,
                            "args": fallback_data,
                            "raw_response": message
                        }

                return {
                    "decision": "hold_position",
                    "args": {"symbol": market_data.get('symbol', 'UNKNOWN'), "reason": f"AI ({self.model}) returned text only."},
                    "raw_response": message
                }

        except Exception as e:
            self.logger.error(f"Error calling AI ({self.model}): {e}")
            return None

    def _parse_fallback_json(self, content):
        import re
        try:
            match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if match: return json.loads(match.group(1))
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if match: return json.loads(match.group(1))
        except: pass
        return None
