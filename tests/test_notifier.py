import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from engine.notifier import Notifier

@pytest.fixture
def mock_env():
    with patch.dict('os.environ', {'DISCORD_WEBHOOK_URL': 'http://test-webhook.com'}):
        yield

@pytest.mark.asyncio
async def test_send_trade_alert_no_webhook():
    with patch.dict('os.environ', {}, clear=True):
        notifier = Notifier()
        assert notifier.webhook_url is None

        with patch.object(notifier.logger, 'info') as mock_info:
            await notifier.send_trade_alert("AAPL", "BUY", 10, 150.0, 140.0, "Test")
            mock_info.assert_called_once_with("No Discord Webhook configured. Skipping notification.")

@pytest.mark.asyncio
async def test_send_trade_alert_success(mock_env):
    notifier = Notifier()
    assert notifier.webhook_url == 'http://test-webhook.com'

    with patch('engine.notifier.asyncio.to_thread') as mock_to_thread:
        mock_response = MagicMock()
        mock_to_thread.return_value = mock_response

        with patch.object(notifier.logger, 'info') as mock_info:
            await notifier.send_trade_alert("AAPL", "BUY", 10, 150.0, 140.0, "Test reason")

            mock_to_thread.assert_called_once()
            args, kwargs = mock_to_thread.call_args

            # verify payload structure
            payload = kwargs.get('json')
            assert payload is not None
            assert payload["username"] == "AI Trader"
            assert len(payload["embeds"]) == 1
            embed = payload["embeds"][0]
            assert embed["title"] == "🚨 TRADE ALERT: BUY AAPL"
            assert embed["color"] == 5763719

            mock_response.raise_for_status.assert_called_once()
            mock_info.assert_called_once_with("Notification sent for AAPL")

@pytest.mark.asyncio
async def test_send_trade_alert_sell_color(mock_env):
    notifier = Notifier()

    with patch('engine.notifier.asyncio.to_thread') as mock_to_thread:
        mock_to_thread.return_value = MagicMock()

        await notifier.send_trade_alert("AAPL", "SELL", 10, 150.0, 160.0, "Test reason")

        _, kwargs = mock_to_thread.call_args
        payload = kwargs.get('json')
        assert payload["embeds"][0]["color"] == 15548997
        assert payload["embeds"][0]["title"] == "🚨 TRADE ALERT: SELL AAPL"

@pytest.mark.asyncio
async def test_send_trade_alert_failure(mock_env):
    notifier = Notifier()

    with patch('engine.notifier.asyncio.to_thread') as mock_to_thread:
        mock_to_thread.side_effect = Exception("Network error")

        with patch.object(notifier.logger, 'error') as mock_error:
            await notifier.send_trade_alert("AAPL", "BUY", 10, 150.0, 140.0, "Test")

            mock_error.assert_called_once_with("Failed to send notification: Network error")
