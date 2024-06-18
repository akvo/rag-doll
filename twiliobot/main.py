import os
import logging
import json
import asyncio
from datetime import datetime

from quart import Quart, request
from Akvo_rabbitmq_client import rabbitmq_client
from twiliobot_client import twiliobot_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)


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


async def initialize_rabbitmq():
    try:
        await rabbitmq_client.initialize()
    except Exception as e:
        logger.error(f"Error initializing RabbitMQ: {e}")


@app.before_serving
async def before_server_start():
    await initialize_rabbitmq()
    asyncio.create_task(rabbitmq_client.consume_twiliobot(
        callback=twiliobot_client.send_whatsapp_message
    ))


@app.route("/whatsapp", methods=["GET", "POST"])
async def receive_whatsapp_message():
    try:
        values = await request.form
        logger.info(f"Receive Whatsapp msg: {values}")
        body = twilio_POST_to_queue_message(values)
        await initialize_rabbitmq()
        asyncio.create_task(rabbitmq_client.producer(
            body=body,
            routing_key=rabbitmq_client.RABBITMQ_QUEUE_USER_CHATS,
            # reply_to=rabbitmq_client.RABBITMQ_QUEUE_TWILIOBOT_REPLIES
        ))
        logger.info(f"Message sent to RabbitMQ: {body}")
    except Exception as e:
        logger.error(f"Error receive Whatsapp msg: {values}: {e}")
        return f"Internal error: {type(e)} - {e}", 500
    return "I'll look into it..."


if __name__ == "__main__":
    port = int(os.environ.get("TWILIO_BOT_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)
