import pytest

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from routes.slack_routes import slackbot_client, rabbitmq_client


@pytest.fixture
def mock_slack_client(mocker):
    mocker.patch.object(slackbot_client, "slack_handler", AsyncMock())
    # Mock slack_app and its event handlers
    slack_app_mock = AsyncMock()
    mock_event_handler = AsyncMock()

    async def mock_message_event_handler(event, client):
        print("mock_message_event_handler called with event:", event)
        slackbot_client.format_to_queue_message(event=event)
        await rabbitmq_client.initialize()
        await rabbitmq_client.producer(
            body="mock_queue_message",
            routing_key="mock_queue_chats",
        )
        await slackbot_client.start_onboarding("U67890", "C12345")

    mock_event_handler.side_effect = mock_message_event_handler
    slack_app_mock.event_handlers = {"message": [mock_event_handler]}

    mocker.patch.object(slackbot_client, "slack_app", slack_app_mock)
    mocker.patch.object(
        slackbot_client,
        "format_to_queue_message",
        return_value="mock_queue_message",
    )
    mocker.patch.object(slackbot_client, "start_onboarding", AsyncMock())


async def test_slack_events_endpoint(mock_slack_client, client: TestClient):
    response = await client.post(
        "/slack/events",
        json={"type": "event_callback", "event": {"type": "message"}},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_message_event(
    mock_slack_client,
    run_app,
):
    event = {"channel": "C12345", "user": "U67890"}
    await slackbot_client.slack_app.event_handlers["message"][0](
        event, client=AsyncMock()
    )

    slackbot_client.format_to_queue_message.assert_called_once_with(
        event=event
    )
    slackbot_client.start_onboarding.assert_awaited_once_with(
        "U67890", "C12345"
    )
