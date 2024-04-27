import os
import re
import json
import logging
from time import sleep
from typing import Callable
from datetime import datetime, timezone

from slack_sdk import WebClient
from slack_bolt import App, Say, BoltContext

import pika
from pika.exceptions import StreamLostError

logging.basicConfig(level=logging.DEBUG)

# --- RabbitMQ Section

RABBITMQ_QUEUE_USER_CHATS=os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES=os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES")

def connect_and_create_queue():
    pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_DEFAULT_USER"), os.getenv("RABBITMQ_DEFAULT_PASS"))
    pika_parameters = pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"),
                                                int(os.getenv("RABBITMQ_PORT")),
                                                '/', pika_credentials)
    pika_connection = pika.BlockingConnection(pika_parameters)
    return pika_connection.channel()

user_chat_queue = connect_and_create_queue()
user_chat_queue.queue_declare(queue=RABBITMQ_QUEUE_USER_CHATS)

user_chat_reply_queue = connect_and_create_queue()
user_chat_reply_queue.queue_declare(queue=RABBITMQ_QUEUE_USER_CHAT_REPLIES)

# --- Slack section

app = App(token=os.environ.get("SLACK_BOT_TOKEN"),
          signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

def slack_event_to_queue_message(slack_event: dict) -> str:
    timestamp = float(slack_event.get("thread_ts", None) or slack_event["ts"])
    iso_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

    queue_message = {
      'id': slack_event['client_msg_id'],
      'timestamp': iso_timestamp,
      'platform': 'SLACK',
      'from': {
                'user': slack_event['user'],
                'channel': slack_event['channel']
              }, # XXX test in all forms
      'text': slack_event['text']
    }
    return json.dumps(queue_message)

@app.middleware
def log_request(logger: logging.Logger, body: dict, next: Callable):
    logger.debug(body)
    return next()


# middleware function
def extract_subtype(body: dict, context: BoltContext, next: Callable):
    context["subtype"] = body.get("event", {}).get("subtype", None)
    next()


# Here we try to publish the message on the queue, reconnecting if necessary. We
# also inform the user of any issues we see. Not the ideal solution, but good
# enough for now.
def publish_reliably(queue_message: str, say: Say) -> None:
    global user_chat_queue

    retries = 5
    while retries > 0:
        retries = retries - 1

        try:
            user_chat_queue.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE_USER_CHATS, body=queue_message)
            return
        except StreamLostError:
            say(":pleading_face: oops, looks like I should reconnect first...")
        except Exception as e:
            say(f":pleading_face: that dit not work, let me try again.\n    `{type(e)}: {e}`")

        sleep(5)
        user_chat_queue = connect_and_create_queue()


# https://api.slack.com/events/message
# Newly posted messages only
# or @app.event("message")
@app.event({"type": "message", "subtype": None})
def reply_in_thread(body: dict, say: Say):
    event = body["event"]
    queue_message = slack_event_to_queue_message(event)

    publish_reliably(queue_message, say)
    thread_ts = event.get("thread_ts", None) or event["ts"]
    say("working on it...")


# https://api.slack.com/events/message/file_share
# https://api.slack.com/events/message/bot_message
@app.event(
    event={"type": "message", "subtype": re.compile("(me_message)|(file_share)")},
    middleware=[extract_subtype],
)
def add_reaction(body: dict, client: WebClient, context: BoltContext, logger: logging.Logger):
    subtype = context["subtype"]  # by extract_subtype
    logger.info(f"subtype: {subtype}")
    message_ts = body["event"]["ts"]
    api_response = client.reactions_add(
        channel=context.channel_id,
        timestamp=message_ts,
        name="eyes",
    )
    logger.info(f"api_response: {api_response}")


# This listener handles all uncaught message events
# (The position in source code matters)
@app.event({"type": "message"}, middleware=[extract_subtype])
def just_ack(logger, context):
    subtype = context["subtype"]  # by extract_subtype
    logger.info(f"{subtype} is ignored")


app.start(port=int(os.getenv('SLACK_BOT_PORT')))

