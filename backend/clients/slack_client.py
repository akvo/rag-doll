import os
import json
import logging

from datetime import datetime, timezone
from slack_bolt import App as SlackApp
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from .slack_onboarding import OnboardingTutorial


# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackBotClient:
    def __init__(self):
        # Environment variables for Slack
        self.SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
        self.SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
        # Initialize the Slack app
        self.slack_app = SlackApp(
            token=self.SLACK_BOT_TOKEN,
            signing_secret=self.SLACK_SIGNING_SECRET
        )
        # Slack request handler
        self.slack_handler = SlackRequestHandler(self.slack_app)
        # Initialize the WebClient
        self.client = WebClient(token=self.SLACK_BOT_TOKEN)
        # In-memory storage for onboarding tutorials
        self.onboarding_tutorials_sent = {}

    def start_onboarding(self, user_id: str, channel: str, client: WebClient):
        logger.info(
            f"Starting onboarding for user {user_id} in channel {channel}")
        onboarding_tutorial = OnboardingTutorial(channel)
        message = onboarding_tutorial.get_message_payload()
        response = client.chat_postMessage(**message)
        onboarding_tutorial.timestamp = response["ts"]
        if channel not in self.onboarding_tutorials_sent:
            self.onboarding_tutorials_sent[channel] = {}
        self.onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial
        logger.info(
            f"Onboarding message sent to user {user_id} in channel {channel}")

    def format_to_queue_message(self, event: dict) -> str:
        timestamp = float(event.get("thread_ts", None) or event["ts"])
        iso_timestamp = datetime.fromtimestamp(
            timestamp, tz=timezone.utc).isoformat()
        queue_message = {
            'id': event.get('client_msg_id'),
            'timestamp': iso_timestamp,
            'platform': 'SLACK',
            'from': {
                'user': event.get('user'),
                'channel': event.get('channel')
            },
            'text': event['text']
        }
        return json.dumps(queue_message)

    def send_message(self, body: str):
        logger.warning(body)
        try:
            queue_message = json.loads(body)
            text = queue_message["text"]
            channel = queue_message["from"]["channel"]
            response = self.client.chat_postMessage(channel=channel, text=text)
            ts = response['ts']
            logger.info(
                f"Message sent to channel {channel} with timestamp {ts}")
            return response
        except SlackApiError as e:
            logger.error(f"Error sending message: {e.response['error']}")
            raise RuntimeError(
                f"Error sending message to channel {channel}: {e.response[
                    'error']}") from e
