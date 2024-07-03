import os
import logging
from slack_bolt import App as SlackApp
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.web import WebClient
from .slack_onboarding import OnboardingTutorial

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables for Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Initialize the Slack app
slack_app = SlackApp(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Slack request handler
slack_handler = SlackRequestHandler(slack_app)

# In-memory storage for onboarding tutorials
onboarding_tutorials_sent = {}


def start_onboarding(user_id: str, channel: str, client: WebClient):
    logger.info(f"Starting onboarding for user {user_id} in channel {channel}")
    onboarding_tutorial = OnboardingTutorial(channel)
    message = onboarding_tutorial.get_message_payload()
    response = client.chat_postMessage(**message)
    onboarding_tutorial.timestamp = response["ts"]
    if channel not in onboarding_tutorials_sent:
        onboarding_tutorials_sent[channel] = {}
    onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial
    logger.info(
        f"Onboarding message sent to user {user_id} in channel {channel}")
