import os
import socketio
import logging
import json

from Akvo_rabbitmq_client import rabbitmq_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv('RABBITMQ_QUEUE_USER_CHAT_REPLIES')
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
    """Receive a chat message from FE as a reply"""
    logger.info(f"Server received: sid[{sid}] msg: {msg}")
    await rabbitmq_client.producer(
        body=json.dumps(msg),
        routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
        reply_to=None)


async def user_chats_callback(body: str):
    """Listen message from clients and send to socket"""
    message = json.loads(body)
    logger.info(f"Send user_chats_callback into socket: {message}")
    await sio_server.emit('chats', message)
