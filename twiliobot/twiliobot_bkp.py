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
from twilio.twiml.messaging_response import MessagingResponse

from flask import Flask, request

import pika

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
user_chat_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)
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
            phone = queue_message['to']['phone']
            if '+' not in str(phone):
                phone = f"+{phone}"
            logging.info(f"sending '{text}' to WhatsApp number {phone}")
            response = twilio_client.messages.create(
                from_='whatsapp:+14155238886', # XXX externalise
                body=text[:1500],              # XXX chunk on paragraphs instead of [:1600]
                to=f"whatsapp:{phone}"
            )
            logging.warning('XXXX ' + str(response))
            # Check the response status instead of subscripting
            if response.error_code is not None:
                logging.error(f"Failed to send message to WhatsApp number {phone}: {response.error_message}")
        except Exception as e:
            logging.error(f"{type(e)} while sending message to Twilio: {e}")

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
            logging.warning(f"error publishing message: {type(e)}: {e}")

        sleep(5)
        user_chat_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)


def twilio_POST_to_queue_message(values: dict) -> str:
    iso_timestamp = datetime.now().isoformat()

    queue_message = {
      'id': values['MessageSid'],
      'timestamp': iso_timestamp,
      'platform': 'WHATSAPP',
      'from': {
          'phone': values['From'].split(':')[1],
      },
      'text': values['Body']
    }
    return json.dumps(queue_message)


twilio_app = Flask(__name__)

@twilio_app.route("/whatsapp", methods=["GET", "POST"])
def on_whatsapp_message():
    try:
        publish_reliably(twilio_POST_to_queue_message(request.values))

        logging.warning(str(request.values))
        num_media = int(request.values.get("NumMedia"))
    except Exception as e:
        return f"internal error {type(e)}: {e}", 500
    # XXX can I not respond?
    response = MessagingResponse()
    msg = response.message("I'll look into it...")
    return str(response)


# --- threads management and main program

# No runner for Flask, it uses a signalling feature that is only available on
# the main interpreter thread.

twilio_send_thread = threading.Thread(target=twilio_send_runner)
twilio_send_thread.start()

twilio_app.run(host="0.0.0.0", port=os.getenv('TWILIO_BOT_PORT'), debug=True)
twilio_send_thread.join()

