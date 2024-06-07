import os
import json
import threading
from time import sleep
import logging

from twilio.rest import Client
import pika

# --- Configuration ---

logging.basicConfig(level=logging.INFO)

# Load environment variables for RabbitMQ and Twilio configuration
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv("RABBITMQ_QUEUE_USER_CHAT_REPLIES")
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'  # Consider externalizing


# --- RabbitMQ Section ---
def connect_and_create_queue(queue: str):
    """
    Connect to RabbitMQ and create a queue.
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        RABBITMQ_HOST, RABBITMQ_PORT, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    return channel


# Initialize RabbitMQ queues
user_chat_queue = connect_and_create_queue(RABBITMQ_QUEUE_USER_CHATS)
user_chat_reply_queue = connect_and_create_queue(
    RABBITMQ_QUEUE_USER_CHAT_REPLIES)


# --- Twilio send section ---
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def chunk_text_by_paragraphs(text, max_length):
    """
    Split text into chunks by paragraphs,
    ensuring each chunk is within the max_length.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # +2 for the \n\n
        if len(current_chunk) + len(paragraph) + 2 <= max_length:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def twilio_send_runner() -> None:
    """
    Consume messages from the RabbitMQ queue and send them via Twilio.
    """
    def on_message(ch, method, properties, body) -> None:
        """
        Callback function to handle messages received from RabbitMQ.
        """
        try:
            logging.info(f"Message received: {body}")
            queue_message = json.loads(body.decode('utf8'))
            text = queue_message['text']
            phone = queue_message['to']['phone']
            if '+' not in str(phone):
                phone = f"+{phone}"

            # Chunk the text by paragraphs
            chunks = chunk_text_by_paragraphs(text, 1500)
            logging.info(f"sending '{text}' to WhatsApp number {phone}")
            for chunk in chunks:
                logging.info(f"sending '{chunk}' to WhatsApp number {phone}")
                response = twilio_client.messages.create(
                    from_=TWILIO_WHATSAPP_FROM,
                    body=chunk,
                    to=f"whatsapp:{phone}"
                )
                if response.error_code is not None:
                    logging.error(
                        f"Failed to send message to WhatsApp number {phone}: {
                            response.error_message}")

        except Exception as e:
            logging.error(f"Error while sending message to Twilio: {e}")

    while True:
        try:
            user_chat_queue.basic_consume(
                queue=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
                auto_ack=True,
                on_message_callback=on_message)
            user_chat_queue.start_consuming()
        except Exception as e:
            logging.warning(
                f"Reconnecting {RABBITMQ_QUEUE_USER_CHAT_REPLIES}: {e}")
            sleep(5)
            connect_and_create_queue(RABBITMQ_QUEUE_USER_CHAT_REPLIES)
            # user_chat_reply_queue = connect_and_create_queue(
            #     RABBITMQ_QUEUE_USER_CHAT_REPLIES)


# --- threads management and main program ---
# Start the Twilio send thread
twilio_send_thread = threading.Thread(target=twilio_send_runner)
twilio_send_thread.start()

# Ensure the send thread completes before exiting
twilio_send_thread.join()
