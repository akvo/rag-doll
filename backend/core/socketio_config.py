import os
import socketio
import logging
import json

from Akvo_rabbitmq_client import rabbitmq_client, queue_message_util
from http.cookies import SimpleCookie
from utils.jwt_handler import verify_jwt_token
from fastapi import HTTPException
from models import (
    Chat_Session,
    User,
    Client,
    Sender_Role_Enum,
    Platform_Enum,
    Chat,
)
from core.database import engine
from sqlmodel import Session, select
from datetime import datetime, timezone


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
db_session = Session(engine)


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
        logger.info(f"User sid[{sid}] connected")
    except HTTPException as e:
        logger.error(f"User sid[{sid}] can't connect: {e}")


@sio_server.on("disconnect")
async def sio_disconnect(sid):
    logger.info(f"User sid[{sid}] disconnected")


@sio_server.on("chats")
async def chat_message(sid, msg):
    logger.info(f"Server received: sid[{sid}] msg: {msg}")
    # Receive a user chat message from FE and put in chat replies queue
    conversation_envelope = msg.get("conversation_envelope", {})
    async with sio_server.session(sid) as session:
        user_phone_number = session.get("user_phone_number", None)
        client_phone_number = conversation_envelope.get(
            "client_phone_number", None
        )
        # check conversation exists with client phone & user phone number
        conversation_exist = db_session.exec(
            select(Chat_Session)
            .join(User)
            .join(Client)
            .where(
                User.phone_number == user_phone_number,
                Client.phone_number == client_phone_number,
            )
        ).first()
        if conversation_exist:
            iso_timestamp = datetime.now(timezone.utc).isoformat()
            sender_role = conversation_envelope.get("sender_role", None)
            platform = conversation_envelope.get("platform", None)
            # format message into queue message
            queue_message = queue_message_util.create_queue_message(
                message_id=conversation_envelope.get("message_id"),
                client_phone_number=client_phone_number,
                user_phone_number=user_phone_number,
                sender_role=(
                    Sender_Role_Enum[sender_role.upper()]
                    if sender_role
                    else sender_role
                ),
                sender_role_enum=Sender_Role_Enum,
                platform=(
                    Platform_Enum[platform.upper()] if platform else platform
                ),
                platform_enum=Platform_Enum,
                body=msg.get("body"),
                media=msg.get("media"),
                context=msg.get("context"),
                transformation_log=msg.get("transformation_log"),
                timestamp=iso_timestamp,
            )
            logger.info(f"Transform into queue message: {queue_message}")
            await rabbitmq_client.producer(
                body=json.dumps(queue_message),
                routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            )
        else:
            logger.error(
                f"Conversation not exist: user[{user_phone_number}], "
                f"client[{client_phone_number}]"
            )


async def user_chats_callback(body: str):
    # Listen client messages from queue and send to socket io
    message = json.loads(body)
    conversation_envelope = message.get("conversation_envelope", {})
    client_phone_number = conversation_envelope.get(
        "client_phone_number", None
    )
    sender_role = conversation_envelope.get("sender_role", None)
    message_body = message.get("body", None)
    # check if prev conversation for the incoming message exist
    prev_conversation_exist = db_session.exec(
        select(Chat_Session)
        .join(Client)
        .where(Client.phone_number == client_phone_number)
    ).first()
    chat_session_id = prev_conversation_exist.id

    if not prev_conversation_exist:
        # create a new conversation and assign into lowest user id
        user = db_session.exec(select(User).order_by(User.id)).first()

        new_client = Client(client_phone_number=client_phone_number)
        db_session.add(new_client)
        db_session.commit()

        new_chat_session = Chat_Session(
            user_id=user.id, client_id=new_client.id
        )
        db_session.add(new_chat_session)
        db_session.commit()

        chat_session_id = new_chat_session.id
        db_session.flush()
    else:
        # update the existing conversation
        prev_conversation_exist.last_read = datetime.now(timezone.utc)
        db_session.add(prev_conversation_exist)
        db_session.commit()
        db_session.refresh(prev_conversation_exist)

    # save message body into chat table
    new_chat = Chat(
        chat_session_id=chat_session_id,
        message=message_body,
        sender_role=(
            Sender_Role_Enum[sender_role.upper()]
            if sender_role
            else sender_role
        ),
    )
    db_session.add(new_chat)
    db_session.commit()
    db_session.flush()

    # format queue message to send into FE
    if "user_phone_number" in conversation_envelope:
        conversation_envelope.pop("user_phone_number")
    message.pop("conversation_envelope")
    message.update({"conversation_envelope": conversation_envelope})
    logger.info(f"Send transformed user_chats_callback into socket: {message}")
    await sio_server.emit("chats", message)
