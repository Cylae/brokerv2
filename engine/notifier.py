import aiohttp
import logging
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.logger = logging.getLogger(__name__)

    async def send_trade_alert(self, symbol, action, quantity, price, stop_loss, reason):
        """Sends a trade alert to Discord."""
        if not self.webhook_url:
            self.logger.info("No Discord Webhook configured. Skipping notification.")
            return

        embed = {
            "title": f"🚨 TRADE ALERT: {action} {symbol}",
            "color": 5763719 if action == "BUY" else 15548997, # Green for Buy, Red for Sell
            "fields": [
                {"name": "Quantity", "value": str(quantity), "inline": True},
                {"name": "Price", "value": f"${price:.2f}", "inline": True},
                {"name": "Stop Loss", "value": f"${stop_loss:.2f}", "inline": True},
                {"name": "Reason", "value": reason, "inline": False}
            ],
            "footer": {"text": "AI Trading Bot"}
        }

        payload = {
            "username": "AI Trader",
            "embeds": [embed]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    response.raise_for_status()
                    self.logger.info(f"Notification sent for {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
