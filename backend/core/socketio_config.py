import os
import socketio
import logging
import json
import pytz

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
    Chat_Status_Enum,
    Subscription,
    VAPID_PRIVATE_KEY,
    VAPID_CLAIMS,
)
from core.database import engine
from sqlmodel import Session, select, and_
from datetime import datetime, timezone
from fastapi import HTTPException
from socketio.exceptions import ConnectionRefusedError
from utils.util import get_value_or_raise_error
from clients.twilio_client import TwilioClient
from clients.slack_client import SlackBotClient
from db import add_media, check_24h_window
from typing import Optional, List
from pywebpush import webpush, WebPushException
from utils.util import (
    generate_message_template_lang_by_phone_number,
    get_template_content_from_json,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


RABBITMQ_QUEUE_USER_CHATS = os.getenv("RABBITMQ_QUEUE_USER_CHATS")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)
LAST_MESSAGES_LIMIT = int(os.getenv("LAST_MESSAGES_LIMIT", 10))
ASSISTANT_LAST_MESSAGES_LIMIT = int(
    os.getenv("ASSISTANT_LAST_MESSAGES_LIMIT", 10)
)
INITIAL_CHAT_TEMPLATE = os.getenv(
    "INITIAL_CHAT_TEMPLATE",
    "Hi {farmer_name}, I'm {officer_name} the extension officer.",
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
tz = timezone.utc


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


async def save_chat_history(
    session: Session,
    conversation_envelope: dict,
    message_body: str,
    media: Optional[List[dict]] = [],
):
    TESTING = os.getenv("TESTING")
    try:
        user_phone_number = get_value_or_raise_error(
            conversation_envelope, "user_phone_number"
        )
        client_phone_number = get_value_or_raise_error(
            conversation_envelope, "client_phone_number"
        )
        timestamp = get_value_or_raise_error(
            conversation_envelope, "timestamp"
        )
        platform = get_value_or_raise_error(conversation_envelope, "platform")

        # If timestamp is provided, parse it
        if timestamp:
            created_at = datetime.fromisoformat(timestamp)
            # Ensure the datetime is in UTC
            if created_at.tzinfo is not None:
                created_at = created_at.astimezone(pytz.utc)
            else:
                created_at = created_at.replace(tzinfo=pytz.utc)
        else:
            # If timestamp is not provided,
            # it will default to current UTC time in the model
            created_at = datetime.now(tz)  # Let the model handle the default

        conversation_exist = session.exec(
            select(Chat_Session)
            .join(User)
            .join(Client)
            .where(
                User.phone_number == user_phone_number,
                Client.phone_number == client_phone_number,
            )
        ).first()

        if not conversation_exist:
            # TODO :: handle this correctly
            return None

        # user/officer message mark as READ
        new_chat_status = Chat_Status_Enum.READ

        # get message template lang
        message_template_lang = generate_message_template_lang_by_phone_number(
            phone_number=client_phone_number
        )
        send_conversation_reconnect_template = check_24h_window(
            session=session, chat_session_id=conversation_exist.id
        )
        # Send conversation reconnect template if beyond 24hr
        if (
            platform == Platform_Enum.WHATSAPP.value
            and send_conversation_reconnect_template
        ):
            # user/officer message mark as READ
            # TODO ::
            # new_chat_status = Chat_Status_Enum.AWAITING_USER_REPLY

            # get message template ID
            content_sid = os.getenv(
                f"CONVERSATION_RECONNECT_TEMPLATE_{message_template_lang}"
            )
            # send conversation reconnect template
            client = session.exec(
                select(Client).where(
                    Client.phone_number == client_phone_number
                )
            ).first()
            # farmer name
            client_name = (
                client.properties.name
                if client and client.properties
                else client_phone_number
            )
            # save conversation reconnect template chat to database
            # get message template from twilio
            template_content = get_template_content_from_json(
                content_sid=content_sid
            )
            conversation_reconnect_message = f"Hi {client_name},\n"
            conversation_reconnect_message += "Please reply this message"
            conversation_reconnect_message += " to restart your conversation."
            if template_content and not TESTING:
                conversation_reconnect_message = template_content.replace(
                    "{{1}}", client_name
                )
            system_chat = Chat(
                chat_session_id=conversation_exist.id,
                message=conversation_reconnect_message,
                sender_role=Sender_Role_Enum.SYSTEM,
                status=Chat_Status_Enum.READ,
                created_at=created_at,
            )
            session.add(system_chat)
            session.commit()
            # send
            if content_sid and not TESTING:
                await twilio_client.whatsapp_message_template_create(
                    to=client_phone_number,
                    content_variables={"1": client_name},
                    content_sid=content_sid,
                )

        # save user/client chat to database
        sender_role = get_value_or_raise_error(
            conversation_envelope, "sender_role"
        )
        new_chat = Chat(
            chat_session_id=conversation_exist.id,
            message=message_body,
            sender_role=Sender_Role_Enum[sender_role.upper()],
            status=new_chat_status,
            created_at=created_at,
        )
        session.add(new_chat)
        session.commit()

        # handle media
        if media:
            add_media(session=session, chat=new_chat, media=media)
        # eol handle media

        session.flush()

        return {
            "chat_id": new_chat.id,
            "chat_session_id": new_chat.chat_session_id,
            "send_conversation_reconnect_template": (
                send_conversation_reconnect_template
            ),
        }
    except Exception as e:
        logger.error(f"Save chat history failed: {e}")
        raise e
    finally:
        session.close()


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
        sender_role = get_value_or_raise_error(
            conversation_envelope, "sender_role"
        )
        platform = get_value_or_raise_error(conversation_envelope, "platform")

        timestamp = conversation_envelope.get("timestamp", None)
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()

        queue_message = queue_message_util.create_queue_message(
            chat_session_id=conversation_exist.id,
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
            timestamp=timestamp,
        )
        return queue_message
    return conversation_exist


async def handle_incoming_message(session: Session, message: dict):
    conversation_envelope = get_value_or_raise_error(
        message, "conversation_envelope"
    )

    client_phone_number = get_value_or_raise_error(
        conversation_envelope, "client_phone_number"
    )
    sender_role = get_value_or_raise_error(
        conversation_envelope, "sender_role"
    )
    platform = get_value_or_raise_error(conversation_envelope, "platform")

    media = get_value_or_raise_error(message, "media")

    prev_conversation_exist = session.exec(
        select(Chat_Session)
        .join(Client)
        .where(Client.phone_number == client_phone_number)
    ).first()

    send_initial_message = False
    if not prev_conversation_exist:
        send_initial_message = True
        user = session.exec(select(User).order_by(User.id)).first()

        curr_client = session.exec(
            select(Client).where(Client.phone_number == client_phone_number)
        ).first()

        if curr_client:
            client = curr_client
        else:
            client = Client(
                phone_number=int(
                    "".join(filter(str.isdigit, client_phone_number))
                )
            )
            session.add(client)
            session.commit()

        new_chat_session = Chat_Session(
            user_id=user.id,
            client_id=client.id,
            platform=platform,
        )
        session.add(new_chat_session)
        session.commit()

        chat_session_id = new_chat_session.id
        session.flush()
    else:
        send_initial_message = False
        user = prev_conversation_exist.user
        client = prev_conversation_exist.client
        chat_session_id = prev_conversation_exist.id

    new_chat = Chat(
        chat_session_id=chat_session_id,
        message=get_value_or_raise_error(message, "body"),
        sender_role=(Sender_Role_Enum[sender_role.upper()]),
        created_at=datetime.now(tz),
    )
    session.add(new_chat)
    session.commit()

    # handle media
    if media:
        add_media(session=session, chat=new_chat, media=media)
    # eol handle media

    # send & save initial message into chat table
    client_name = (
        client.properties.name if client.properties else client.phone_number
    )
    if send_initial_message:
        user_name = (
            user.properties.name if user.properties else user.phone_number
        )
        initial_message = INITIAL_CHAT_TEMPLATE.format(
            farmer_name=client_name, officer_name=user_name
        )
        new_chat = Chat(
            chat_session_id=chat_session_id,
            message=initial_message,
            sender_role=Sender_Role_Enum.SYSTEM,
            created_at=datetime.now(tz),
        )
        session.add(new_chat)
        session.commit()
        if not os.getenv("TESTING"):
            await twilio_client.whatsapp_message_create(
                to=client.phone_number, body=initial_message
            )
    session.flush()

    user = user.serialize()
    return (
        user["id"],
        user["phone_number"],
        chat_session_id,
        new_chat.id,
        new_chat.status.value,
        client_name,
    )


def handle_read_message(session: Session, chat_session_id: int):
    try:
        unread_messages = session.exec(
            select(Chat).where(
                and_(
                    Chat.chat_session_id == chat_session_id,
                    Chat.status == Chat_Status_Enum.UNREAD,
                )
            )
        ).all()
        for um in unread_messages:
            um.status = Chat_Status_Enum.READ
        session.commit()

        # update chat_session last_read
        chat_session = session.exec(
            select(Chat_Session).where(Chat_Session.id == chat_session_id)
        ).first()
        if chat_session:
            chat_session.last_read = datetime.now(tz)
            session.commit()
        session.flush()
        return unread_messages
    except Exception as e:
        logger.error(f"Error handle read message: {e}")
        raise e


async def resend_messages(session: Session, user_id=int, user_sid=str):
    """
    This function is to resend N last message to platform
    """
    chat_session = session.exec(
        select(Chat_Session).where(Chat_Session.user_id == user_id)
    ).all()
    if not chat_session:
        return None
    last_chats = session.exec(
        select(Chat)
        .where(
            Chat.chat_session_id.in_([cs.id for cs in chat_session]),
        )
        .order_by(Chat.created_at.desc())
        .limit(LAST_MESSAGES_LIMIT)
    ).all()
    # Reorder the results by created_at in ascending order
    last_chats = sorted(last_chats, key=lambda x: x.created_at)
    for chat in last_chats:
        # starting to resend message
        media = []
        context = []
        if chat.media:
            for cm in chat.media:
                media.append({"url": cm.url, "type": cm.type})
                context.append(
                    {
                        "url": cm.url,
                        "type": cm.type,
                        "caption": chat.message,
                    }
                )
        message = queue_message_util.create_queue_message(
            chat_session_id=chat.chat_session_id,
            message_id=chat.id,
            client_phone_number=f"+{chat.chat_session.client.phone_number}",
            user_phone_number=f"+{chat.chat_session.client.phone_number}",
            sender_role=chat.sender_role,
            sender_role_enum=Sender_Role_Enum,
            platform=chat.chat_session.platform,
            platform_enum=Platform_Enum,
            body=chat.message,
            media=media,
            context=context,
            timestamp=chat.created_at.isoformat(),
            status=chat.status.value,
        )
        if chat.sender_role == Sender_Role_Enum.CLIENT:
            await sio_server.emit(
                "chats", message, to=user_sid, callback=emit_chats_callback
            )
            logger.info(f"Resend message for client->user: {message}")
        if chat.sender_role == Sender_Role_Enum.ASSISTANT:
            await sio_server.emit(
                "whisper", message, to=user_sid, callback=emit_whisper_callback
            )
            logger.info(f"Resend message for assistant->user: {message}")
    return last_chats


def get_chat_history_for_assistant(
    session: Session, chat_session_id: int, body: str
):
    last_chats = session.exec(
        select(Chat)
        .where(
            and_(
                Chat.chat_session_id == chat_session_id,
                Chat.sender_role.in_(
                    [
                        Sender_Role_Enum.USER,
                        Sender_Role_Enum.CLIENT,
                        Sender_Role_Enum.ASSISTANT,
                    ]
                ),
            )
        )
        .order_by(Chat.created_at.desc())
        .offset(1)  # skip the latest message
        .limit(ASSISTANT_LAST_MESSAGES_LIMIT)  # retrieve the next N messages
    ).all()
    if not last_chats:
        return body
    # append history to message body
    body = json.loads(body)
    # Reorder the results by created_at in ascending order
    last_chats = sorted(last_chats, key=lambda x: x.created_at)
    history = [lc.to_assistant_history() for lc in last_chats]
    body.update({"history": history})
    body = json.dumps(body)
    return body


async def user_to_client(body: str):
    """
    This function (functionally) routes messages that come in from the user to
    the client. It is responsible to take all the steps needed. For user to
    client routing, the message is posted onto the channel that the conversation
    is happening on.
    """
    session = Session(engine)
    queue_message = json.loads(body)
    conversation_envelope = queue_message.get("conversation_envelope", {})
    platform = conversation_envelope.get("platform")
    text = queue_message.get("body")
    media = queue_message.get("media", [])

    send_conversation_reconnect_template = False
    if not os.getenv("TESTING"):
        # save outgoing chat
        res = await save_chat_history(
            session=session,
            conversation_envelope=conversation_envelope,
            message_body=text,
            media=media,
        )
        # eol save outgoing chat
        send_conversation_reconnect_template = res.get(  # noqa
            "send_conversation_reconnect_template"
        )
    if (
        platform
        == Platform_Enum.WHATSAPP.value
        # TODO ::
        # and not send_conversation_reconnect_template
    ):
        await twilio_client.send_whatsapp_message(body=body)
    if platform == Platform_Enum.SLACK.value:
        await slackbot_client.send_message(body=body)


@sio_server.on("connect")
async def sio_connect(sid, environ):
    try:
        session = Session(engine)
        httpCookie = environ.get("HTTP_COOKIE")
        if not httpCookie:
            return None
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
            await resend_messages(
                session=session, user_id=user_id, user_sid=sid
            )
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
                    "message": "Message processed and sent",
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


@sio_server.on("read_message")
async def read_message(sid, chat_session_id):
    session = Session(engine)
    handle_read_message(session=session, chat_session_id=chat_session_id)


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

        (
            user_id,
            user_phone_number,
            chat_session_id,
            chat_id,
            chat_status,
            client_name,
        ) = await handle_incoming_message(session=session, message=message)

        user_sid = get_cache(user_id=user_id)

        conversation_envelope = get_value_or_raise_error(
            message, "conversation_envelope"
        )
        conversation_envelope.update({"user_phone_number": user_phone_number})
        conversation_envelope.update({"chat_session_id": chat_session_id})
        conversation_envelope.update({"message_id": chat_id})
        conversation_envelope.update({"status": chat_status})
        message.pop("conversation_envelope", None)
        message.update({"conversation_envelope": conversation_envelope})

        # add history to queue
        body = get_chat_history_for_assistant(
            session=session, chat_session_id=chat_session_id, body=body
        )
        # eol add history to queue

        # send message to user_chats
        await rabbitmq_client.producer(
            body=body,
            routing_key=RABBITMQ_QUEUE_USER_CHATS,
        )
        await sio_server.emit(
            "chats", message, to=user_sid, callback=emit_chats_callback
        )

        # Send push notification
        subscriptions = session.exec(
            select(Subscription).where(Subscription.user_id == user_id)
        ).all()
        body_text = message.get("body")
        max_length = 150
        # Truncate and add ellipsis if needed
        truncated_body = (
            (body_text[:max_length] + "...")
            if len(body_text) > max_length
            else body_text
        )
        for subscription in subscriptions:
            try:
                if (
                    "updates.push.services.mozilla.com"
                    in subscription.endpoint
                ):
                    VAPID_CLAIMS.update(
                        {"aud": "https://updates.push.services.mozilla.com"}
                    )
                elif "fcm.googleapis.com" in subscription.endpoint:
                    VAPID_CLAIMS.update({"aud": "https://fcm.googleapis.com"})
                else:
                    VAPID_CLAIMS.update({"aud": ""})
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": json.loads(subscription.keys),
                    },
                    data=json.dumps(
                        {
                            "title": client_name,
                            "body": truncated_body,
                        }
                    ),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS,
                )
            except WebPushException as e:
                # Detect if the subscription is invalid or expired
                if e.response.status_code in {404, 410}:
                    logger.warning(
                        "Removing invalid subscription:", subscription.endpoint
                    )
                    # Remove the invalid subscription from the database
                    session.delete(subscription)
                    session.commit()
                else:
                    logger.error(
                        f"Failed to send notification {subscription.endpoint}:",
                        e,
                    )
        # EOL send push notification

        logger.info(
            f"Send client->user to {USER_CACHE_KEY}{user_id} "
            f"{user_sid}: {message}"
        )

    except Exception as e:
        logger.error(f"Error handling client_to_user: {e}")
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

        (
            user_id,
            user_phone_number,
            chat_session_id,
            chat_id,
            chat_status,
            client_name,
        ) = await handle_incoming_message(session=session, message=message)
        user_sid = get_cache(user_id=user_id)

        conversation_envelope = get_value_or_raise_error(
            message, "conversation_envelope"
        )
        conversation_envelope.update({"user_phone_number": user_phone_number})
        conversation_envelope.update({"chat_session_id": chat_session_id})
        conversation_envelope.update({"message_id": chat_id})
        conversation_envelope.update({"status": chat_status})
        message.pop("conversation_envelope", None)
        message.update({"conversation_envelope": conversation_envelope})

        await sio_server.emit(
            "whisper", message, to=user_sid, callback=emit_whisper_callback
        )
        logger.info(
            f"Send assistant->user to {USER_CACHE_KEY}{user_id} "
            f"{user_sid}: {message}"
        )

    except Exception as e:
        logger.error(f"Error handling assistant_to_user: {e}")
        raise e
