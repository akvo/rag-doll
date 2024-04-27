import os
import re
import json
import logging
from typing import Callable

from slack_sdk import WebClient
from slack_bolt import App, Say, BoltContext

import pika

logging.basicConfig(level=logging.DEBUG)

# --- RabbitMQ Section

pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_DEFAULT_USER"), os.getenv("RABBITMQ_DEFAULT_PASS"))
pika_parameters = pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"),
                                            int(os.getenv("RABBITMQ_PORT")),
                                            '/', pika_credentials)
pika_connection = pika.BlockingConnection(pika_parameters)
user_chat_queue = pika_connection.channel()

queue_name = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
user_chat_queue.queue_declare(queue=queue_name)

# --- Slack section

app = App(token=os.environ.get("SLACK_BOT_TOKEN"),
          signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

def slack_event_to_queue_message(slack_event: dict) -> str:
    queue_message = {
      'id': slack_event['client_msg_id'],
      'timestamp': event.get("thread_ts", None) or event["ts"], # XXX to ISO8601
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


# https://api.slack.com/events/message
# Newly posted messages only
# or @app.event("message")
@app.event({"type": "message", "subtype": None})
def reply_in_thread(body: dict, say: Say):
    event = body["event"]
    user_chat_queue.basic_publish(exchange='', routing_key=queue_name, body=slack_event_to_queue_message(event))

    thread_ts = event.get("thread_ts", None) or event["ts"]
    say(text="working on it...", thread_ts=thread_ts) # XXX So how do we get answers back?


@app.event(
    event={"type": "message", "subtype": "message_deleted"},
    matchers=[
        # Skip the deletion of messages by this listener
        lambda body: "You've deleted a message: "
        not in body["event"]["previous_message"]["text"]
    ],
)
def detect_deletion(say: Say, body: dict):
    text = body["event"]["previous_message"]["text"]
    say(f"You've deleted a message: {text}")


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


# XXX
# @slack_events.on('message')
# def on_message(payload):
#     event = payload.get('event')
#
#     channel = event.get('channel')
#     user = event.get('user')
#     text = event.get('text')
#
#     print(f"{user}{channel}: {text}")

app.start(port=int(os.getenv('SLACK_BOT_PORT')))

