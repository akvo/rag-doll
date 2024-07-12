import os
import socketio
import logging
import json

from Akvo_rabbitmq_client import rabbitmq_client
from http.cookies import SimpleCookie
from utils.jwt_handler import verify_jwt_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)
SOCKETIO_PATH = ""

sio_server = socketio.AsyncServer(
    async_mode="asgi",
)

sio_app = socketio.ASGIApp(
    socketio_server=sio_server, socketio_path=SOCKETIO_PATH
)

cookie = SimpleCookie()


@sio_server.on("connect")
async def sio_connect(sid, environ):
    # TODO :: We can use AUTH_TOKEN in websocket
    # should we implement this?
    cookie.load(environ["HTTP_COOKIE"])
    auth_token = cookie["AUTH_TOKEN"].value
    user_phone_number = verify_jwt_token(auth_token).get("uphone_number")
    logger.info(f"A user sid[{sid}] connected, {user_phone_number}")


@sio_server.on("disconnect")
async def sio_disconnect(sid):
    logger.info(f"User sid[{sid}] disconnected")


@sio_server.on("chats")
async def chat_message(sid, msg):
    """Receive a user chat message from FE and put in chat replies queue"""
    logger.info(f"Server received: sid[{sid}] msg: {msg}")
    await rabbitmq_client.producer(
        body=json.dumps(msg),
        routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
    )


async def user_chats_callback(body: str):
    """Listen client messages from queue and send to socket io"""
    message = json.loads(body)
    logger.info(f"Send user_chats_callback into socket: {message}")
    await sio_server.emit("chats", message)
