import os
import re
import json
import threading
from time import sleep
from typing import Callable
from datetime import datetime, timezone

import logging
logging.basicConfig(level=logging.INFO)

from slack_sdk import WebClient
from slack_bolt import App, Say, BoltContext

import pika
from pika.exceptions import StreamLostError

# --- RabbitMQ Section

def connect_and_create_queue(queue: str):
    pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASS"))
    pika_parameters = pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"),
                                                int(os.getenv("RABBITMQ_PORT")),
                                                '/', pika_credentials)
    pika_connection = pika.BlockingConnection(pika_parameters)
    q = pika_connection.channel()
    q.queue_declare(queue=queue)
    return q

RABBITMQ_QUEUE_USER_CHATS=os.getenv("RABBITMQ_QUEUE_USER_CHATS")
user_chat_queue       = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)
RABBITMQ_QUEUE_USER_CHAT_REPLIES=os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES")
user_chat_reply_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHAT_REPLIES)


# --- Slack receive section

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
        user_chat_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)


def slack_receive_runner() -> None:
    slack_app = App(token=os.getenv("SLACK_BOT_TOKEN"),
                    signing_secret=os.getenv("SLACK_SIGNING_SECRET"))

    @slack_app.event("message")
    def reply_in_thread(body: dict, say: Say):
        event = body["event"]
        queue_message = slack_event_to_queue_message(event)

        publish_reliably(queue_message, say)

    slack_app.start(port=int(os.getenv('SLACK_BOT_PORT')))


# --- Slack send section

slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def slack_send_runner() -> None:
    def on_message(ch, method, properties, body) -> None:
        try:
            logging.info(f"Message received: ch: {ch}, method: {method}, properties: {properties}, body: {body}")
            queue_message = json.loads(body.decode('utf8'))

            text = queue_message['text']
            channel = queue_message['to']['channel']
            logging.info(f"sending '{text}' to Slack channel {channel}")
            response = slack_client.chat_postMessage(text=text, channel=channel)
            if response['error']:
                logging.error(f"Failed to send message to Slack channel {channel}: {response['error']}")
        except Exception as e:
            logging.error(f"{type(e)} while sending message to Slack: {e}")


    while True:
        try:
            user_chat_queue.basic_consume(queue=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                                          auto_ack=True,
                                          on_message_callback=on_message)
            user_chat_queue.start_consuming()
        except Exception as e:
            logging.warning(f"reconnecting {RABBITMQ_QUEUE_USER_CHAT_REPLIES}: {type(e)}: {e}")
            sleep(5)
            user_chat_reply_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHAT_REPLIES)


# --- threads management and main program

slack_receive_thread = threading.Thread(target=slack_receive_runner)
slack_receive_thread.start()
slack_send_thread = threading.Thread(target=slack_send_runner)
slack_send_thread.start()

slack_receive_thread.join()
slack_send_thread.join()

