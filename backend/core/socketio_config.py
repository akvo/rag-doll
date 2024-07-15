import os
import socketio
import logging
import json

from Akvo_rabbitmq_client import rabbitmq_client
from http.cookies import SimpleCookie
from utils.jwt_handler import verify_jwt_token
from fastapi import HTTPException

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
    try:
        cookie.load(environ["HTTP_COOKIE"])
        auth_token = cookie["AUTH_TOKEN"].value
        user_phone_number = verify_jwt_token(auth_token).get(
            "uphone_number", None
        )
        async with sio_server.session(sid) as session:
            session["user_phone_number"] = user_phone_number
        logger.info(f"A user sid[{sid}] connected, {user_phone_number}")
    except HTTPException as e:
        logger.error(f"User sid[{sid}] can't connect: {e}")


@sio_server.on("disconnect")
async def sio_disconnect(sid):
    logger.info(f"User sid[{sid}] disconnected")


@sio_server.on("chats")
async def chat_message(sid, msg):
    # Receive a user chat message from FE and put in chat replies queue
    async with sio_server.session(sid) as session:
        user_phone_number = session.get("user_phone_number", None)
        # TODO :: check that conversation exists with client phone & user phone
        logger.info(
            f"Server received: sid[{sid}] msg: {msg}, {user_phone_number}"
        )
        await rabbitmq_client.producer(
            body=json.dumps(msg),
            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
        )


async def user_chats_callback(body: str):
    # Listen client messages from queue and send to socket io
    message = json.loads(body)
    conversation_envelope = message.get("conversation_envelope")
    for key in [
        "conversation_id",
        "user_phone_number",
        "platform",
    ]:
        conversation_envelope.pop(key)
    message.pop("conversation_envelope")
    message.update({"conversation_envelope": conversation_envelope})
    logger.info(f"Send transformed user_chats_callback into socket: {message}")
    await sio_server.emit("chats", message)
