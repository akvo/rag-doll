import json
import phonenumbers
from os import environ
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from sqlmodel import Session, select
from uuid import uuid4
from datetime import timedelta

from pydantic_extra_types.phone_numbers import PhoneNumber
from models import User
from models.chat import Sender_Role_Enum, Platform_Enum
from core.database import get_session
from utils.jwt_handler import create_jwt_token
from clients.twilio_client import TwilioClient
from Akvo_rabbitmq_client import queue_message_util
from middleware import verify_user


router = APIRouter()
security = HTTPBearer()

webdomain = environ.get("WEBDOMAIN")
MAGIC_LINK_CHAT_TEMPLATE = environ.get("MAGIC_LINK_CHAT_TEMPLATE")

twilio_client = TwilioClient()


@router.post("/login")
async def send_login_link(
    phone_number: PhoneNumber, session: Session = Depends(get_session)
):
    phone_number = phonenumbers.parse(phone_number)
    phone_number = (
        f"+{phone_number.country_code}{phone_number.national_number}"
    )
    user = session.exec(
        select(User).where(User.phone_number == phone_number)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    login_code_uuid = uuid4()
    user.login_code = str(login_code_uuid)
    session.commit()

    # format login link and message for the user
    link = f"{webdomain}/verify/{user.login_code}"
    message_body = queue_message_util.create_queue_message(
        message_id=str(uuid4()),
        user_phone_number=phone_number,
        sender_role=Sender_Role_Enum.SYSTEM,
        sender_role_enum=Sender_Role_Enum,
        platform=Platform_Enum.WHATSAPP,
        platform_enum=Platform_Enum,
        body=MAGIC_LINK_CHAT_TEMPLATE.format(magic_link=link),
    )
    twilio_client.send_whatsapp_message(body=json.dumps(message_body))
    return {"message": "Login link sent via WhatsApp"}


@router.get("/verify/{login_code:path}")
async def verify_login_code(
    login_code: str, session: Session = Depends(get_session)
):
    user = session.exec(
        select(User).where(User.login_code == login_code)
    ).first()
    if not user:
        raise HTTPException(
            status_code=400, detail="Invalid verification UUID"
        )
    login_token = create_jwt_token(
        {
            "uid": user.id,
            "uphone_number": user.phone_number,
        },
        expires_delta=timedelta(hours=2),
    )
    user.login_code = None
    session.commit()
    res = user.serialize()
    res.update(
        {
            "token": login_token,
        }
    )
    return res


@router.get("/me")
async def user_me(
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)
    return user.serialize()
