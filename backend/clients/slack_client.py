import os
import logging

from slack_bolt import App as SlackApp
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.web import WebClient
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
