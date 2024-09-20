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
from clients.twilio_client import TwilioClient
from clients.slack_client import SlackBotClient
from db import add_media


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)


def get_rabbitmq_client():
    return rabbitmq_client


SOCKETIO_PATH = ""

twilio_client = TwilioClient()
slackbot_client = SlackBotClient()

sio_server = socketio.AsyncServer(
    async_mode="asgi",
    ping_interval=130,  # 130 seconds
    ping_timeout=120,  # 120 seconds
    transports=["websocket", "polling"],
)
sio_app = socketio.ASGIApp(
    socketio_server=sio_server, socketio_path=SOCKETIO_PATH
)

cookie = SimpleCookie()


USER_CACHE_DICT = {}
USER_CACHE_KEY = "USER_"


def set_cache(user_id: str, sid: str):
    key = f"{USER_CACHE_KEY}{user_id}"
    logger.info(f"[FastAPICache] Setting cache: {key} -> {sid}")
    USER_CACHE_DICT[key] = sid


def get_cache(user_id: str):
    key = f"{USER_CACHE_KEY}{user_id}"
    sid = USER_CACHE_DICT.get(key)
    logger.info(f"[FastAPICache] Retrieved cache: {key} -> {sid}")
    return sid


def delete_cache(user_id: str):
    key = f"{USER_CACHE_KEY}{user_id}"
    logger.info(f"[FastAPICache] delete_cache: {key}")
    if key in USER_CACHE_DICT:
        del USER_CACHE_DICT[key]


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

    media = get_value_or_raise_error(message, "media")

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

    # handle media
    if media:
        add_media(session=session, chat=new_chat, media=media)
    # eol handle media

    session.flush()
    return str(user_id)


async def user_to_client(body: str):
    """
    This function (functionally) routes messages that come in from the user to
    the client. It is responsible to take all the steps needed. For user to
    client routing, the message is posted onto the channel that the conversation
    is happening on.
    """
    queue_message = json.loads(body)
    conversation_envelope = queue_message.get("conversation_envelope", {})
    platform = conversation_envelope.get("platform")
    if platform == Platform_Enum.WHATSAPP.value:
        twilio_client.send_whatsapp_message(body=body)
    if platform == Platform_Enum.SLACK.value:
        await slackbot_client.send_message(body=body)


@sio_server.on("connect")
async def sio_connect(sid, environ):
    try:
        httpCookie = environ.get("HTTP_COOKIE")
        if not httpCookie:
            return False
        cookie.load(httpCookie)
        auth_token = cookie.get("AUTH_TOKEN")
        auth_token = auth_token.value if auth_token else None
        decoded_token = verify_jwt_token(auth_token)
        user_phone_number = decoded_token.get("uphone_number")
        user_id = decoded_token.get("uid")
        async with sio_server.session(sid) as sio_session:
            sio_session["user_id"] = user_id
            sio_session["user_phone_number"] = user_phone_number
            set_cache(user_id=user_id, sid=sid)
        logger.info(f"User sid[{sid}] connected: {user_phone_number}")
    except HTTPException as e:
        logger.error(f"User sid[{sid}] can't connect: {e}")
        raise ConnectionRefusedError("Authentication failed")
    except Exception as e:
        logger.error(f"SIO Connection Error: {e}")
        raise e


@sio_server.on("disconnect")
async def sio_disconnect(sid):
    async with sio_server.session(sid) as sio_session:
        user_id = sio_session.get("user_id")
        if user_id:
            delete_cache(user_id=user_id)
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
                await user_to_client(json.dumps(queue_message))
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


async def client_to_user(body: str):
    """
    This function (functionally) routes messages that come in from clients to
    the user. It is responsible to take all the steps needed. For client to user
    routing, that means it should send the message to the assistant as well as
    send it to the user's frontend.
    """
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

        user_sid = get_cache(user_id=user_id)

        logger.info(
            f"Send client->user to {USER_CACHE_KEY}{user_id} "
            f"{user_sid}: {message}"
        )

        await sio_server.emit(
            "chats", message, to=user_sid, callback=emit_chats_callback
        )

        await rabbitmq_client.initialize()
        await rabbitmq_client.producer(
            body=body,
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
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


async def assistant_to_user(body: str):
    """
    This function (functionally) routes messages that come in from the assistant
    to the user. It is responsible to take all the steps needed. For assistant
    to user routing, the message is marked as a whisper and posted to the
    frontend.
    """
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

        user_sid = get_cache(user_id=user_id)

        logger.info(
            f"Send assistant->user to {USER_CACHE_KEY}{user_id} "
            f"{user_sid}: {message}"
        )

        await sio_server.emit(
            "whisper", message, to=user_sid, callback=emit_whisper_callback
        )
    except Exception as e:
        logger.error(f"Error handling user_chats_callback: {e}")
        raise e
