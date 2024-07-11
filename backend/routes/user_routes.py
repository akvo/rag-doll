import json
import phonenumbers
from os import environ
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from uuid import uuid4
from datetime import timedelta

from pydantic_extra_types.phone_numbers import PhoneNumber
from models import User
from models.chat import Chat_Sender, PlatformEnum
from core.database import get_session
from utils.jwt_handler import create_jwt_token
from Akvo_rabbitmq_client import rabbitmq_client, queue_message_util


router = APIRouter()
webdomain = environ.get("WEBDOMAIN")
RABBITMQ_QUEUE_USER_CHAT_REPLIES = environ.get(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)
MAGIC_LINK_CHAT_TEMPLATE = environ.get("MAGIC_LINK_CHAT_TEMPLATE")


@router.post("/login")
async def send_login_link(
    phone_number: PhoneNumber, session: Session = Depends(get_session)
):
    phone_number = phonenumbers.parse(phone_number)
    phone_number = f"+{phone_number.country_code}{phone_number.national_number}"
    user = session.exec(
        select(User).where(User.phone_number == phone_number)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    login_code_uuid = uuid4()
    user.login_code = str(login_code_uuid)
    session.commit()
    # send login link into queue
    link = f"{webdomain}/verify/{user.login_code}"
    message_body = queue_message_util.create_queue_message(
        message_id=str(uuid4()),
        conversation_id=str(uuid4()),
        user_phone_number=phone_number,
        sender_role=Chat_Sender.SYSTEM,
        sender_role_enum=Chat_Sender,
        platform=PlatformEnum.WHATSAPP,
        platform_enum=PlatformEnum,
        body=MAGIC_LINK_CHAT_TEMPLATE.format(magic_link=link),
    )
    await rabbitmq_client.producer(
        body=json.dumps(message_body),
        routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES
    )
    # return {"message": "Login link sent via WhatsApp"}
    return f"{webdomain}/verify/{user.login_code}"


@router.get("/verify/{login_code:path}")
async def verify_login_code(
    login_code: str, session: Session = Depends(get_session)
):
    user = session.exec(
        select(User).where(User.login_code == login_code)
    ).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification UUID")
    login_token = create_jwt_token(
        {"sub": str(user.login_code), "uid": user.id},
        expires_delta=timedelta(hours=2),
    )
    user.login_code = None
    session.commit()
    return {"token": login_token}
