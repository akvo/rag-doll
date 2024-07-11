import os
import json
import logging

from datetime import datetime, timezone
from slack_bolt.async_app import AsyncApp as SlackApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from .slack_onboarding import OnboardingMessage
from Akvo_rabbitmq_client import queue_message_util
from models.chat import PlatformEnum, Chat_Sender


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackBotClient:
    def __init__(self):
        self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
        self.SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
        self.slack_app = SlackApp(
            token=self.SLACK_BOT_TOKEN,
            signing_secret=self.SLACK_SIGNING_SECRET,
        )
        self.slack_handler = AsyncSlackRequestHandler(self.slack_app)
        self.client = AsyncWebClient(token=self.SLACK_BOT_TOKEN)
        # TODO ::
        # How do we want to handle onboarding message logs?
        # For now, we use an in-memory log to check whether the onboarding
        # message has been sent to a Slack user.
        self.onboarding_message_sent = {}

    async def start_onboarding(self, user_id: str, channel: str):
        onboarding_message = OnboardingMessage(channel)
        if channel not in self.onboarding_message_sent:
            self.onboarding_message_sent[channel] = {}
        if user_id not in self.onboarding_message_sent[channel]:
            message = onboarding_message.get_message_payload()
            response = await self.client.chat_postMessage(**message)
            onboarding_message.timestamp = response["ts"]
            logger.info(
                f"Onboarding message sent to user {user_id} "
                f" in channel {channel}"
            )
        self.onboarding_message_sent[channel][user_id] = onboarding_message

    def format_to_queue_message(self, event: dict) -> str:
        timestamp = float(event.get("thread_ts", None) or event["ts"])
        iso_timestamp = datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        ).isoformat()
        queue_message = queue_message_util.create_queue_message(
            message_id=event.get("client_msg_id"),
            conversation_id=event.get("channel"),
            client_phone_number=event.get("user"),
            sender_role=Chat_Sender.CLIENT,
            sender_role_enum=Chat_Sender,
            platform=PlatformEnum.SLACK,
            platform_enum=PlatformEnum,
            body=event.get("text"),
            timestamp=iso_timestamp,
        )
        return json.dumps(queue_message)

    async def send_message(self, body: str):
        try:
            queue_message = json.loads(body)
            conversation_envelope = queue_message.get(
                "conversation_envelope", {}
            )
            text = queue_message.get("body")
            channel = conversation_envelope.get("conversation_id")
            response = await self.client.chat_postMessage(
                channel=channel, text=text
            )
            ts = response["ts"]
            logger.info(
                f"Message sent to channel {channel} with timestamp {ts}"
            )
            return response
        except SlackApiError as e:
            error = (
                f"Error sending message to channel {channel}:"
                f" {e.response['error']}"
            )
            logger.error(error)
            raise RuntimeError(error) from e
