import json
import pytest

from unittest.mock import patch
from clients.slack_client import SlackBotClient, OnboardingTutorial
from slack_sdk.errors import SlackApiError


@pytest.fixture
def slack_bot_client():
    return SlackBotClient()


@patch("slack_sdk.web.async_client.AsyncWebClient")
async def test_start_onboarding(mock_async_web_client, slack_bot_client):
    mock_async_web_client.chat_postMessage.return_value = {"ts": "1234567890"}
    onboarding_tutorial = OnboardingTutorial("channel")
    onboarding_tutorial.get_message_payload.return_value = {"key": "value"}
    await slack_bot_client.start_onboarding("user_id", "channel")
    mock_async_web_client.chat_postMessage.assert_awaited_once_with(
        key="value"
    )
    assert (
        slack_bot_client.onboarding_tutorials_sent["channel"][
            "user_id"
        ].timestamp
        == "1234567890"
    )


def test_format_to_queue_message(slack_bot_client):
    event = {
        "ts": 1643723400,
        "client_msg_id": "client_msg_id",
        "user": "user",
        "channel": "channel",
        "text": "text",
    }
    queue_message = slack_bot_client.format_to_queue_message(event)
    res = json.loads(queue_message)
    assert res == {
        "conversation_envelope": {
            "message_id": "client_msg_id",
            "conversation_id": "channel",
            "client_phone_number": "user",
            "user_phone_number": None,
            "sender_role": "client",
            "platform": "SLACK",
            "timestamp": "2022-02-01T13:50:00+00:00",
        },
        "body": "text",
        "media": [],
        "context": [],
        "transformation_log": ["text"],
    }


@patch("slack_sdk.web.async_client.AsyncWebClient")
async def test_send_message(mock_async_web_client, slack_bot_client):
    mock_async_web_client.chat_postMessage.return_value = {"ts": "1234567890"}
    body = json.dumps(
        {
            "id": "client_msg_id",
            "timestamp": "2022-02-01T12:30:00+00:00",
            "platform": "SLACK",
            "from": {"user": "user", "channel": "channel"},
            "text": "text",
        }
    )
    response = await slack_bot_client.send_message(body)
    mock_async_web_client.chat_postMessage.assert_awaited_once_with(
        channel="channel", text="text"
    )
    assert response == {"ts": "1234567890"}


@patch("slack_sdk.web.async_client.AsyncWebClient")
async def test_send_message_slack_api_error(
    mock_async_web_client, slack_bot_client
):
    mock_async_web_client.chat_postMessage.side_effect = SlackApiError(
        response={"error": "error"}
    )
    body = json.dumps(
        {
            "id": "client_msg_id",
            "timestamp": "2022-02-01T12:30:00+00:00",
            "platform": "SLACK",
            "from": {"user": "user", "channel": "channel"},
            "text": "text",
        }
    )
    with pytest.raises(RuntimeError):
        await slack_bot_client.send_message(body)
