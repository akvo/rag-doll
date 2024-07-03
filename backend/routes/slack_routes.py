import os
import logging

from fastapi import APIRouter, Request
from fastapi.security import HTTPBearer
from clients.slack_client import SlackBotClient
from Akvo_rabbitmq_client import rabbitmq_client


# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

slackbot_client = SlackBotClient()
slack_app = slackbot_client.slack_app

router = APIRouter()
security = HTTPBearer()

RABBITMQ_QUEUE_SLACKBOT_REPLIES = os.getenv('RABBITMQ_QUEUE_SLACKBOT_REPLIES')
RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')


@router.post("/slack/events")
async def endpoint(req: Request):
    return await slackbot_client.slack_handler.handle(req)


@slack_app.event("team_join")
def onboarding_message(event, client):
    user_id = event.get("user", {}).get("id")
    logger.info(f"New team join event for user {user_id}")
    response = client.conversations_open(users=user_id)
    channel = response["channel"]["id"]
    logger.info(f"Channel {channel} opened for user {user_id}")
    slackbot_client.start_onboarding(user_id, channel, client)


@slack_app.event("reaction_added")
def update_emoji(event, client):
    channel_id = event.get("item", {}).get("channel")
    user_id = event.get("user")
    logger.info(
        f"Reaction added event in channel {channel_id} by user {user_id}")
    if channel_id not in slackbot_client.onboarding_tutorials_sent:
        logger.warning(f"No onboarding tutorial found for channel {channel_id}")
        return
    onboarding_tutorial = slackbot_client.onboarding_tutorials_sent[
        channel_id][user_id]
    onboarding_tutorial.reaction_task_completed = True
    message = onboarding_tutorial.get_message_payload()
    client.chat_update(**message)


@slack_app.event("pin_added")
def update_pin(event, client):
    channel_id = event.get("channel_id")
    user_id = event.get("user")
    logger.info(f"Pin added event in channel {channel_id} by user {user_id}")
    onboarding_tutorial = slackbot_client.onboarding_tutorials_sent[
        channel_id][user_id]
    onboarding_tutorial.pin_task_completed = True
    message = onboarding_tutorial.get_message_payload()
    client.chat_update(**message)


@slack_app.event("message")
async def message(event, client):
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    queue_msg = slackbot_client.format_to_queue_message(event=event)
    # Send message to RabbitMQ
    await rabbitmq_client.producer(
        body=queue_msg,
        routing_key=RABBITMQ_QUEUE_USER_CHATS,
        reply_to=RABBITMQ_QUEUE_SLACKBOT_REPLIES
    )
    logger.info(
        f"Message event in channel {channel_id} by user {user_id}: {queue_msg}")
    if text and text.lower() == "start":
        slackbot_client.start_onboarding(user_id, channel_id, client)
