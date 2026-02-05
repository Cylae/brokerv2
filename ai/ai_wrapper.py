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
                # self.logger.warning("AI did not use a tool. Raw content: " + str(message.content))
                return {
                    "decision": "hold_position",
                    "args": {"symbol": market_data['symbol'], "reason": "AI returned text only."},
                    "raw_response": message
                }

        except Exception as e:
            self.logger.error(f"Error calling AI: {e}")
            return None
