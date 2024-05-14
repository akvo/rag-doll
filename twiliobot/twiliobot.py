import os
import re
import json
import threading
from time import sleep
from typing import Callable
from datetime import datetime, timezone

import logging
logging.basicConfig(level=logging.INFO)

from twilio.rest import Client
from flask import Flask, request

import pika

# --- RabbitMQ Section

def connect_and_create_queue(queue: str):
    pika_credentials = pika.PlainCredentials(os.getenv("RABBITMQ_DEFAULT_USER"), os.getenv("RABBITMQ_DEFAULT_PASS"))
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


# --- Twilio send section

twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def twilio_send_runner() -> None:
    def on_message(ch, method, properties, body) -> None:
        try:
            logging.info(f"Message received: ch: {ch}, method: {method}, properties: {properties}, body: {body}")
            queue_message = json.loads(body.decode('utf8'))

            text = queue_message['text']
            channel = queue_message['to']['channel']
            logging.info(f"sending '{text}' to Slack channel {channel}")
            response = twilio_client.messages.create(
                from_='whatsapp:+14155238886', # XXX externalise
                body=text,
                to='whatsapp:+31651838192'     # XXX take from queue message
            )
            print('XXXX ' + str(response))
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


# --- Twilio receive section

# Here we try to publish the message on the queue, reconnecting if necessary. We
# log errors, but don't inform the user of any issues we see. Not the ideal
# solution, but good enough for now.

def publish_reliably(queue_message: str) -> None:
    global user_chat_queue

    retries = 5
    while retries > 0:
        retries = retries - 1

        try:
            user_chat_queue.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE_USER_CHATS, body=queue_message)
            return
        except Exception as e:
            print(f"error publishing message: {type(e)}: {e}")

        sleep(5)
        user_chat_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)


twilio_app = Flask(__name__)

GOOD_BOY_URL = (
    "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?ixlib=rb-1.2.1"
    "&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1350&q=80"
)

@twilio_app.route("/whatsapp", methods=["GET", "POST"])
def on_whatsapp_message():
    try:
        num_media = int(request.values.get("NumMedia"))
    except (ValueError, TypeError):
        return "Invalid request: invalid or missing NumMedia parameter", 400
    response = MessagingResponse()
    if not num_media:
        msg = response.message("Send us an image!")
    else:
        msg = response.message("Thanks for the image. Here's one for you!")
        msg.media(GOOD_BOY_URL)
    return str(response)

    # XXX publish_reliably(queue_message, say)


# --- threads management and main program

# No runner for Flask, it uses a signalling feature that is only available on
# the main interpreter thread.

twilio_send_thread = threading.Thread(target=twilio_send_runner)
twilio_send_thread.start()

twilio_app.run(host="0.0.0.0", port=os.getenv('TWILIO_BOT_PORT'), debug=True)
twilio_send_thread.join()

