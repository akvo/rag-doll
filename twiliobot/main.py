import os
import logging
import asyncio
import threading

from flask import Flask
from Akvo_rabbitmq_client import rabbitmq_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

twilio_app = Flask(__name__)


@twilio_app.route("/whatsapp", methods=["GET", "POST"])
def on_whatsapp_message():
    return {"Hello": "World"}


async def consume_twiliobot_messages():
    try:
        await rabbitmq_client.initialize()
        await rabbitmq_client.consume_twiliobot()
    except Exception as e:
        logging.error(f"Error initializing RabbitMQ in twiliobot app: {e}")


def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


if __name__ == "__main__":
    # Create a new event loop
    loop = asyncio.new_event_loop()
    # Start the event loop in a new thread
    t = threading.Thread(target=start_background_loop, args=(loop,))
    t.start()

    # Schedule the consume_twiliobot_messages coroutine to run in the event loop
    asyncio.run_coroutine_threadsafe(consume_twiliobot_messages(), loop)

    # Start the Flask app
    port = int(os.environ.get("TWILIO_BOT_PORT", 5000))
    twilio_app.run(host="0.0.0.0", port=port, debug=True)
