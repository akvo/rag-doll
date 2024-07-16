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
from sqlalchemy.exc import SQLAlchemyError


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


def check_conversation_exist_and_generate_queue_message(
    session: Session, msg: dict, user_phone_number: str
):
    conversation_envelope = msg.get("conversation_envelope")
    client_phone_number = conversation_envelope.get("client_phone_number")
    conversation_exist = session.exec(
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
        sender_role = conversation_envelope.get("sender_role")
        platform = conversation_envelope.get("platform")
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
        return queue_message
    return conversation_exist


def handle_incoming_message(session: Session, message: dict):
    conversation_envelope = message.get("conversation_envelope")
    client_phone_number = conversation_envelope.get(
        "client_phone_number", None
    )
    sender_role = conversation_envelope.get("sender_role")
    message_body = message.get("body")

    # Check if prev conversation for the incoming message exists
    prev_conversation_exist = session.exec(
        select(Chat_Session)
        .join(Client)
        .where(Client.phone_number == client_phone_number)
    ).first()

    if not prev_conversation_exist:
        # Create a new conversation and assign to the lowest user ID
        user = session.exec(select(User).order_by(User.id)).first()
        new_client = Client(
            phone_number=int("".join(filter(str.isdigit, client_phone_number)))
        )
        session.add(new_client)
        session.commit()

        new_chat_session = Chat_Session(
            user_id=user.id, client_id=new_client.id
        )
        session.add(new_chat_session)
        session.commit()

        chat_session_id = new_chat_session.id
        session.flush()
    else:
        chat_session_id = prev_conversation_exist.id

    # Save message body into chat table
    new_chat = Chat(
        chat_session_id=chat_session_id,
        message=message_body,
        sender_role=(
            Sender_Role_Enum[sender_role.upper()]
            if sender_role
            else sender_role
        ),
    )
    session.add(new_chat)
    session.commit()
    session.flush()


@sio_server.on("connect")
async def sio_connect(sid, environ):
    try:
        cookie.load(environ["HTTP_COOKIE"])
        auth_token = cookie["AUTH_TOKEN"].value
        user_phone_number = verify_jwt_token(auth_token).get("uphone_number")
        async with sio_server.session(sid) as sio_session:
            sio_session["user_phone_number"] = user_phone_number
        logger.info(f"User sid[{sid}] connected")
    except HTTPException as e:
        logger.error(f"User sid[{sid}] can't connect: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


@sio_server.on("disconnect")
async def sio_disconnect(sid):
    logger.info(f"User sid[{sid}] disconnected")


@sio_server.on("chats")
async def chat_message(sid, msg):
    try:
        session = Session(engine)
        logger.info(f"Server received: sid[{sid}] msg: {msg}")
        # Receive a user chat message from FE and put in chat replies queue
        conversation_envelope = msg.get("conversation_envelope")
        async with sio_server.session(sid) as sio_session:
            user_phone_number = sio_session.get("user_phone_number")
            client_phone_number = conversation_envelope.get(
                "client_phone_number"
            )
            # check conversation exists with client phone & user phone number
            queue_message = (
                check_conversation_exist_and_generate_queue_message(
                    session=session,
                    msg=msg,
                    user_phone_number=user_phone_number,
                )
            )
            if queue_message:
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

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def user_chats_callback(body: str):
    # Listen client messages from queue and send to socket io
    try:
        session = Session(engine)
        message = json.loads(body)
        handle_incoming_message(session=session, message=message)
        # format queue message to send into FE
        conversation_envelope = message.get("conversation_envelope")
        conversation_envelope.pop("user_phone_number")
        message.pop("conversation_envelope")
        message.update({"conversation_envelope": conversation_envelope})
        logger.info(
            f"Send transformed user_chats_callback into socket: {message}"
        )
        await sio_server.emit("chats", message)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
