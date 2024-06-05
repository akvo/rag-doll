from os import environ
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from uuid import uuid4
from datetime import timedelta

from models import User
from utils.jwt_handler import create_jwt_token
from core.database import engine

router = APIRouter()
webdomain = environ.get("WEBDOMAIN")


@router.post("/login")
async def send_login_link(phone_number: int):
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.phone_number == phone_number)
        ).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        login_link_uuid = uuid4()
        user.login_link = str(login_link_uuid)
        session.commit()
        # TODO: Implement this function to send WhatsApp messages
        send_whatsapp_message(phone_number, user.login_link)
        # return {"message": "Login link sent via WhatsApp"}
        return {"redirect": f"{webdomain}/verify/{user.login_link}"}


@router.get("/verify")
async def verify_login_link(login_link: str):
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.login_link == login_link)
        ).first()
        if not user:
            raise HTTPException(
                status_code=404, detail="User not found or link expired"
            )
        login_token = create_jwt_token(
            {"sub": str(user.login_link)}, expires_delta=timedelta(hours=2)
        )
        return {"token": login_token}


def send_whatsapp_message(phone_number: int, login_token: str):
    # Implement your WhatsApp API integration here
    pass
