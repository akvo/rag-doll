import phonenumbers
from os import environ
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from sqlmodel import Session, select
from uuid import uuid4
from datetime import timedelta

from pydantic_extra_types.phone_numbers import PhoneNumber
from models import User
from core.database import get_session
from utils.jwt_handler import create_jwt_token
from clients.twilio_client import TwilioClient
from middleware import verify_user


router = APIRouter()
security = HTTPBearer()

webdomain = environ.get("WEBDOMAIN")
MAGIC_LINK_CHAT_TEMPLATE = environ.get("MAGIC_LINK_CHAT_TEMPLATE")

twilio_client = TwilioClient()


@router.post("/login")
async def send_login_link(
    phone_number: PhoneNumber,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
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

    if environ.get("TESTING"):
        return {"message": "Login link sent via WhatsApp"}

    # format login link and message for the user
    link = f"{webdomain}/verify/{user.login_code}"
    background_tasks.add_task(
        twilio_client.whatsapp_message_create,
        to=phone_number,
        body=MAGIC_LINK_CHAT_TEMPLATE.format(magic_link=link),
    )
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
