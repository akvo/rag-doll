import os
import logging

from fastapi import APIRouter, Request
from fastapi.security import HTTPBearer
from clients.slack_client import SlackBotClient
from Akvo_rabbitmq_client import rabbitmq_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

slackbot_client = SlackBotClient()
slack_app = slackbot_client.slack_app

router = APIRouter()
security = HTTPBearer()

RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")


@router.post("/slack/events")
async def endpoint(req: Request):
    return await slackbot_client.slack_handler.handle(req)


@slack_app.event("message")
async def message(event, client):
    channel_id = event.get("channel")
    user_id = event.get("user")
    queue_msg = slackbot_client.format_to_queue_message(event=event)
    # Send incoming message from slack to RabbitMQ queue
    try:
        await rabbitmq_client.initialize()
        await rabbitmq_client.producer(
            body=queue_msg,
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
        )
        logger.info(
            f"Receive message in channel[{channel_id}] "
            f"by user[{user_id}]: {queue_msg}"
        )
        await slackbot_client.start_onboarding(user_id, channel_id)
    except Exception as e:
        logger.error(f"Error handling message event: {e}")
