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

    mock_session = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_post = MagicMock()
    mock_post.return_value.__aenter__.return_value = mock_response
    mock_session.post = mock_post

    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = mock_session

    with patch('engine.notifier.aiohttp.ClientSession', return_value=mock_session_cm):
        with patch.object(notifier.logger, 'info') as mock_info:
            await notifier.send_trade_alert("AAPL", "BUY", 10, 150.0, 140.0, "Test reason")

            assert mock_session.post.call_count == 1
            args, kwargs = mock_session.post.call_args

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

    mock_session = AsyncMock()
    mock_response = MagicMock()
    mock_post = MagicMock()
    mock_post.return_value.__aenter__.return_value = mock_response
    mock_session.post = mock_post

    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = mock_session

    with patch('engine.notifier.aiohttp.ClientSession', return_value=mock_session_cm):
        await notifier.send_trade_alert("AAPL", "SELL", 10, 150.0, 160.0, "Test reason")

        _, kwargs = mock_session.post.call_args
        payload = kwargs.get('json')
        assert payload["embeds"][0]["color"] == 15548997
        assert payload["embeds"][0]["title"] == "🚨 TRADE ALERT: SELL AAPL"

@pytest.mark.asyncio
async def test_send_trade_alert_failure(mock_env):
    notifier = Notifier()

    mock_session = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("Network error")
    mock_post = MagicMock()
    mock_post.return_value.__aenter__.return_value = mock_response
    mock_session.post = mock_post

    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = mock_session

    with patch('engine.notifier.aiohttp.ClientSession', return_value=mock_session_cm):
        with patch.object(notifier.logger, 'error') as mock_error:
            await notifier.send_trade_alert("AAPL", "BUY", 10, 150.0, 140.0, "Test")

            mock_error.assert_called_once_with("Failed to send notification: Network error")
