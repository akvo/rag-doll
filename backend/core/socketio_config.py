import os
import socketio
import logging
import json

from Akvo_rabbitmq_client import rabbitmq_client, queue_message_util
from http.cookies import SimpleCookie
from utils.jwt_handler import verify_jwt_token
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
from fastapi import HTTPException
from socketio.exceptions import ConnectionRefusedError
from utils.util import get_value_or_raise_error
from fastapi_cache import FastAPICache


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)
SOCKETIO_PATH = ""

sio_server = socketio.AsyncServer(async_mode="asgi")
sio_app = socketio.ASGIApp(
    socketio_server=sio_server, socketio_path=SOCKETIO_PATH
)

cookie = SimpleCookie()

USER_CACHE_KEY = "USER_"


async def set_user_session(user_id: str, sid: str):
    await FastAPICache.get_backend().set(f"{USER_CACHE_KEY}{user_id}", sid)


async def get_user_session(user_id: str):
    return await FastAPICache.get_backend().get(f"{USER_CACHE_KEY}{user_id}")


async def delete_user_session(user_id: str):
    await FastAPICache.get_backend().clear(f"{USER_CACHE_KEY}{user_id}")


def check_conversation_exist_and_generate_queue_message(
    session: Session, msg: dict, user_phone_number: str
):
    conversation_envelope = get_value_or_raise_error(
        msg, "conversation_envelope"
    )
    client_phone_number = get_value_or_raise_error(
        conversation_envelope, "client_phone_number"
    )

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
        sender_role = get_value_or_raise_error(
            conversation_envelope, "sender_role"
        )
        platform = get_value_or_raise_error(conversation_envelope, "platform")

        queue_message = queue_message_util.create_queue_message(
            message_id=get_value_or_raise_error(
                conversation_envelope, "message_id"
            ),
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
            body=get_value_or_raise_error(msg, "body"),
            media=get_value_or_raise_error(msg, "media"),
            context=get_value_or_raise_error(msg, "context"),
            transformation_log=get_value_or_raise_error(
                msg, "transformation_log"
            ),
            timestamp=iso_timestamp,
        )
        return queue_message
    return conversation_exist


def handle_incoming_message(session: Session, message: dict):
    conversation_envelope = get_value_or_raise_error(
        message, "conversation_envelope"
    )
    client_phone_number = get_value_or_raise_error(
        conversation_envelope, "client_phone_number"
    )
    sender_role = get_value_or_raise_error(
        conversation_envelope, "sender_role"
    )

    prev_conversation_exist = session.exec(
        select(Chat_Session)
        .join(Client)
        .where(Client.phone_number == client_phone_number)
    ).first()

    if not prev_conversation_exist:
        user = session.exec(select(User).order_by(User.id)).first()
        user_id = user.id

        curr_client = session.exec(
            select(Client).where(Client.phone_number == client_phone_number)
        ).first()

        if curr_client:
            new_client = curr_client
        else:
            new_client = Client(
                phone_number=int(
                    "".join(filter(str.isdigit, client_phone_number))
                )
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
        user_id = prev_conversation_exist.user_id
        chat_session_id = prev_conversation_exist.id

    new_chat = Chat(
        chat_session_id=chat_session_id,
        message=get_value_or_raise_error(message, "body"),
        sender_role=(Sender_Role_Enum[sender_role.upper()]),
    )
    session.add(new_chat)
    session.commit()
    session.flush()
    return user_id


@sio_server.on("connect")
async def sio_connect(sid, environ):
    try:
        cookie.load(environ["HTTP_COOKIE"])
        auth_token = cookie["AUTH_TOKEN"].value
        decoded_token = verify_jwt_token(auth_token)
        user_phone_number = decoded_token.get("uphone_number")
        user_id = decoded_token.get("uid")
        async with sio_server.session(sid) as sio_session:
            sio_session["user_phone_number"] = user_phone_number
            await set_user_session(user_id, sid)
        logger.info(f"User sid[{sid}] connected: {user_id}")
    except HTTPException as e:
        logger.error(f"User sid[{sid}] can't connect: {e}")
        raise ConnectionRefusedError("Authentication failed")
    except Exception as e:
        logger.error(f"SIO Connection Error: {e}")
        raise e


@sio_server.on("disconnect")
async def sio_disconnect(sid):
    async with sio_server.session(sid) as sio_session:
        user_phone_number = sio_session.get("user_phone_number")
        if user_phone_number:
            user_id = user_phone_number  # Adjust if needed
            await delete_user_session(user_id)
    logger.info(f"User sid[{sid}] disconnected")


@sio_server.on("chats")
async def chat_message(sid, msg):
    try:
        session = Session(engine)
        logger.info(f"Server received: sid[{sid}] msg: {msg}")

        conversation_envelope = get_value_or_raise_error(
            msg, "conversation_envelope"
        )
        client_phone_number = get_value_or_raise_error(
            conversation_envelope, "client_phone_number"
        )

        async with sio_server.session(sid) as sio_session:
            user_phone_number = get_value_or_raise_error(
                sio_session, "user_phone_number"
            )

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
                return {
                    "success": True,
                    "message": "Message processed and sent to RabbitMQ",
                }
            else:
                error_message = (
                    f"Conversation not exist: user[{user_phone_number}], "
                    f"client[{client_phone_number}]"
                )
                logger.error(error_message)
                return {"success": False, "message": error_message}
    except Exception as e:
        logger.error(f"Error handling chats event: {e}")
        return {"success": False, "message": str(e)}
    finally:
        session.close()


async def emit_chats_callback(value):
    logger.info(f"Emit chats callback {value}")


async def user_chats_callback(body: str):
    try:
        session = Session(engine)
        message = json.loads(body)

        user_id = handle_incoming_message(session=session, message=message)

        conversation_envelope = get_value_or_raise_error(
            message, "conversation_envelope"
        )
        conversation_envelope.pop("user_phone_number", None)
        message.pop("conversation_envelope", None)
        message.update({"conversation_envelope": conversation_envelope})

        user_sid = await get_user_session(user_id)

        logger.info(
            f"Send user_chats_callback to {USER_CACHE_KEY}{user_id} "
            f"{user_sid}: {message}"
        )

        await sio_server.emit(
            "chats", message, to=user_sid, callback=emit_chats_callback
        )
    except Exception as e:
        logger.error(f"Error handling user_chats_callback: {e}")
        raise e
    finally:
        session.close()


async def emit_whisper_callback(value):
    logger.info(f"Emit whisper callback {value}")


@sio_server.on("whisper")
async def assistant_chat_reply(sid, msg):
    print(sid, msg)


async def assistant_chat_replies_callback(body: str):
    message = json.loads(body)
    await sio_server.emit("whisper", message, callback=emit_whisper_callback)
