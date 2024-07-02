import os
import socketio
import logging
import json

from Akvo_rabbitmq_client import rabbitmq_client, queue_message_util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SOCKETIO_PATH = ""

sio_server = socketio.AsyncServer(
    async_mode='asgi',
)

sio_app = socketio.ASGIApp(
    socketio_server=sio_server,
    socketio_path=SOCKETIO_PATH
)


@sio_server.on('connect')
async def sio_connect(sid, environ):
    """Track user connection"""
    logger.info(f'A user sid[{sid}] connected')


@sio_server.on('disconnect')
async def sio_disconnect(sid):
    """Track user disconnection"""
    logger.info(f'User sid[{sid}] disconnected')


@sio_server.on('chats')
async def chat_message(sid, msg):
    """Receive a chat message and send to all clients"""
    RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
    logger.info(f"Server received: sid[{sid}] msg: {msg}")
    await rabbitmq_client.producer(
        body=json.dumps(msg),
        routing_key=RABBITMQ_QUEUE_USER_CHATS)


async def chat_replies_callback(body: str):
    message = queue_message_util.create_queue_message(
        message_id="use message id from queue",
        conversation_id="use conversation id from queue",
        client_phone_number="+6281234567890",
        user_phone_number="+6282234567899",
        sender="USER",
        body=body,
    )
    logger.info(f"Server received chat_replies_callback: {message}")
    await sio_server.emit(
        'chats',
        message
    )
