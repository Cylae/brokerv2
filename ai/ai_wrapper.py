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
        Enforces Strict Tool Use and validates against Hallucinations.
        """
        target_symbol = market_data.get('symbol', 'UNKNOWN')
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
            decision = None
            args = {}

            # 1. Check for Native Tool Call
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                decision = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to decode JSON from tool call: {tool_call.function.arguments}")
                    decision = None # Invalid JSON

            # 2. Fallback: Check for JSON in Content (Mistral/Gemini Edge Cases)
            if not decision and message.content:
                content = message.content.strip()
                # Remove Markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                # Attempt to find JSON structure
                try:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx+1]
                        parsed = json.loads(json_str)

                        # Heuristic to detect which function it intended
                        if 'function' in parsed and 'name' in parsed['function']:
                            # Structure: {"type": "function", "function": {"name": "...", "arguments": "..."}}
                            decision = parsed['function']['name']
                            raw_args = parsed['function'].get('arguments', parsed['function'].get('parameters', {}))
                            if isinstance(raw_args, str):
                                try:
                                    args = json.loads(raw_args)
                                except:
                                    args = {}
                            else:
                                args = raw_args
                        elif 'name' in parsed and 'parameters' in parsed:
                             decision = parsed['name']
                             args = parsed['parameters']
                        # If it just outputted arguments, we can't be sure of the action.

                        if decision:
                            self.logger.info(f"Recovered JSON Decision from content: {decision}")

                except Exception as e:
                    self.logger.debug(f"JSON Fallback failed: {e}")

            # 3. Default to HOLD if no valid decision
            if not decision:
                self.logger.warning(f"AI ({self.model}) did not use a tool. Content: {message.content[:100]}...")
                return {
                    "decision": "hold_position",
                    "args": {"symbol": target_symbol, "reason": f"AI ({self.model}) returned text only."},
                    "raw_response": message
                }

            # 4. Hallucination Check (CRITICAL)
            # Ensure the symbol in the tool call matches the symbol we analyzed.
            dec_symbol = args.get('symbol', '').upper().replace('/', '')
            tgt_symbol = target_symbol.upper().replace('/', '')

            # Logic: If neither contains the other, it's a mismatch.
            # e.g. BTC vs BTCUSDT (Match), BTC vs ETH (Mismatch)
            if dec_symbol and tgt_symbol:
                if dec_symbol not in tgt_symbol and tgt_symbol not in dec_symbol:
                    self.logger.warning(f"HALLUCINATION DETECTED: Analyzed {target_symbol} but AI decided for {args['symbol']}. FORCING HOLD.")
                    return {
                        "decision": "hold_position",
                        "args": {"symbol": target_symbol, "reason": f"Hallucination Blocked: AI tried to trade {args['symbol']}"},
                        "raw_response": message
                    }

            return {
                "decision": decision,
                "args": args,
                "raw_response": message
            }

        except Exception as e:
            self.logger.error(f"Error calling AI ({self.model}): {e}")
            return None
