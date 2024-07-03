import os
import logging
from slack_bolt import App as SlackApp
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.web import WebClient
from pydantic import BaseModel
from typing import Any
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
    onboarding_tutorial = OnboardingTutorial(channel)
    message = onboarding_tutorial.get_message_payload()
    response = client.chat_postMessage(**message)
    onboarding_tutorial.timestamp = response["ts"]
    if channel not in onboarding_tutorials_sent:
        onboarding_tutorials_sent[channel] = {}
    onboarding_tutorials_sent[channel][user_id] = onboarding_tutorial


@slack_app.event("team_join")
def onboarding_message(event, client):
    user_id = event.get("user", {}).get("id")
    response = client.conversations_open(users=user_id)
    channel = response["channel"]["id"]
    start_onboarding(user_id, channel, client)


@slack_app.event("reaction_added")
def update_emoji(event, client):
    channel_id = event.get("item", {}).get("channel")
    user_id = event.get("user")
    if channel_id not in onboarding_tutorials_sent:
        return
    onboarding_tutorial = onboarding_tutorials_sent[channel_id][user_id]
    onboarding_tutorial.reaction_task_completed = True
    message = onboarding_tutorial.get_message_payload()
    client.chat_update(**message)


@slack_app.event("pin_added")
def update_pin(event, client):
    channel_id = event.get("channel_id")
    user_id = event.get("user")
    onboarding_tutorial = onboarding_tutorials_sent[channel_id][user_id]
    onboarding_tutorial.pin_task_completed = True
    message = onboarding_tutorial.get_message_payload()
    client.chat_update(**message)


@slack_app.event("message")
def message(event, client):
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    if text and text.lower() == "start":
        start_onboarding(user_id, channel_id, client)


class SlackEvent(BaseModel):
    event: dict
    type: str
    challenge: Any = None
