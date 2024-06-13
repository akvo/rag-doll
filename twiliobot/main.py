import os
import logging
import asyncio

from flask import Flask
from rabbitmq_client import rabbitmq_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


twilio_app = Flask(__name__)


@twilio_app.route("/whatsapp", methods=["GET", "POST"])
def on_whatsapp_message():
    # try:
    #     publish_reliably(twilio_POST_to_queue_message(request.values))

    #     logging.warning(str(request.values))
    #     num_media = int(request.values.get("NumMedia"))
    # except Exception as e:
    #     return f"internal error {type(e)}: {e}", 500
    # # XXX can I not respond?
    # response = MessagingResponse()
    # msg = response.message("I'll look into it...")
    # return str(response)
    return {"Hello": "World"}


async def startup_event():
    try:
        await rabbitmq_client.initialize()
        # await rabbitmq_client.consume_reply_to_twiliobot()
        asyncio.create_task(rabbitmq_client.consume_reply_to_twiliobot())
    except Exception as e:
        logging.error(f"Error initializing RabbitMQ in twiliobot app: {e}")


if __name__ == "__main__":
    asyncio.run(startup_event())
    port = int(os.environ.get("TWILIO_BOT_PORT"))
    twilio_app.run(host="0.0.0.0", port=port, debug=True)
