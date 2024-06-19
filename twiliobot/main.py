import os
import logging
import json
import asyncio
from datetime import datetime

from quart import Quart, request, jsonify
from Akvo_rabbitmq_client import rabbitmq_client
from twiliobot_client import twiliobot_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)


RABBITMQ_QUEUE_TWILIOBOT_REPLIES = os.getenv('RABBITMQ_QUEUE_TWILIOBOT_REPLIES')
RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')


# Helper function to format Twilio messages for RabbitMQ
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


@app.before_serving
async def before_server_start():
    await rabbitmq_client.initialize()
    asyncio.create_task(rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_TWILIOBOT_REPLIES,
        routing_key=f"*.{RABBITMQ_QUEUE_TWILIOBOT_REPLIES}",
        callback=twiliobot_client.send_whatsapp_message
    ))


@app.after_serving
async def after_server_stop():
    if rabbitmq_client:
        await rabbitmq_client.disconnect()


@app.post("/whatsapp")
async def receive_whatsapp_message():
    try:
        values = await request.form
        logger.info(f"Received Whatsapp message: {values}")
        body = twilio_POST_to_queue_message(values)
        # Ensure RabbitMQ is initialized before sending message
        await rabbitmq_client.initialize()
        # Send message to RabbitMQ
        asyncio.create_task(rabbitmq_client.producer(
            body=body,
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
            reply_to=RABBITMQ_QUEUE_TWILIOBOT_REPLIES
        ))
        logger.info(f"Message sent to RabbitMQ: {body}")
        return jsonify({"message": "Message received and sent to queue"}), 200

    except Exception as e:
        logger.error(f"Error receiving Whatsapp message: {values}: {e}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500
