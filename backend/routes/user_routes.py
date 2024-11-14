import phonenumbers
from os import environ
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from sqlmodel import Session, select
from uuid import uuid4
from datetime import timedelta

from pydantic_extra_types.phone_numbers import PhoneNumber
from models import User, Chat_Session, Client
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

    # get the region code
    phone_number_region = phonenumbers.region_code_for_number(phone_number)
    phone_number_region = phone_number_region.lower()
    message_template_lang = "en"
    if phone_number_region == "ke":
        message_template_lang = "sw"

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

    user_name = user.properties.name if user.properties else phone_number
    link = f"{webdomain}/verify/{user.login_code}"
    if environ.get("TESTING"):
        return {
            "user_name": user_name,
            "link": link,
            "message_template_lang": message_template_lang,
        }

    content_sid = environ.get(
        f"VERIFICATION_TEMPLATE_ID_{message_template_lang}"
    )
    # format login link and message for the user
    if content_sid:
        background_tasks.add_task(
            twilio_client.whatsapp_message_template_create,
            to=phone_number,
            content_variables={"1": user_name, "2": link},
            content_sid=content_sid,
        )
    else:
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
        expires_delta=timedelta(days=1),
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

    # get the clients of user
    chat_sesssion = session.exec(
        select(Chat_Session).where(Chat_Session.user_id == user.id)
    ).all()
    client_ids = [cs.client_id for cs in chat_sesssion]
    clients = session.exec(
        select(Client).where(Client.id.in_(client_ids))
    ).all()
    clients = [c.serialize() for c in clients]
    # eol get clients

    user = user.serialize()
    user.update({"clients": clients})
    return user
