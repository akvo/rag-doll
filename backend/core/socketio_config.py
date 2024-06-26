import os
import socketio
import logging
import json

from Akvo_rabbitmq_client import rabbitmq_client

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
    logger.info('A user connected')


@sio_server.on('disconnect')
async def sio_disconnect(sid):
    """Track user disconnection"""
    logger.info('User disconnected')


@sio_server.on('chats')
async def chat_message(sid, msg):
    """Receive a chat message and send to all clients"""
    RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
    logger.info(f"Server received: {msg} {RABBITMQ_QUEUE_USER_CHATS}")
    await rabbitmq_client.producer(
        body=json.dumps(msg),
        routing_key=RABBITMQ_QUEUE_USER_CHATS)


async def chats_callback(body: str):
    logger.info(f"Server received chats_callback: {body}")
    await sio_server.emit('chats', json.loads(body))


async def chat_replies_callback(body: str):
    logger.info(f"Server received chat_replies_callback: {body}")
    await sio_server.emit(
        'chats',
        {
            "phone": "+628123456789",
            "reply": body,
        }
    )
