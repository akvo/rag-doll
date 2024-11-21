import os
import phonenumbers

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from models import (
    Chat_Session,
    Chat,
    Sender_Role_Enum,
    Chat_Status_Enum,
    Client,
    Platform_Enum,
)
from sqlmodel import Session, select, func, and_
from middleware import verify_user
from core.database import get_session
from pydantic import BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import List
from clients.twilio_client import TwilioClient
from datetime import datetime, timezone
from db import get_last_message, check_24h_window

router = APIRouter()
security = HTTPBearer()

twilio_client = TwilioClient()
tz = timezone.utc


class BroadcastRequest(BaseModel):
    contacts: List[PhoneNumber]
    message: str


@router.get("/chat-list")
async def get_chats(
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    user = verify_user(session, auth)

    total_chats = session.exec(
        select(func.count(Chat_Session.id)).where(
            Chat_Session.user_id == user.id
        )
    ).one()

    if offset >= total_chats:
        raise HTTPException(
            status_code=404, detail="Offset exceeds total number of chats"
        )

    chats = session.exec(
        select(Chat_Session)
        .where(Chat_Session.user_id == user.id)
        .order_by(Chat_Session.last_read.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    last_chats = []
    for chat in chats:
        # count of unread message
        unread_messages = session.exec(
            select(Chat.id).where(
                and_(
                    Chat.chat_session_id == chat.id,
                    Chat.status == Chat_Status_Enum.UNREAD,
                    Chat.sender_role == Sender_Role_Enum.CLIENT,
                )
            )
        ).all()
        unread_message_count = len(unread_messages)

        # unread_assistant_message
        unread_assistant_message = session.exec(
            select(Chat.id)
            .where(
                and_(
                    Chat.chat_session_id == chat.id,
                    Chat.status == Chat_Status_Enum.UNREAD,
                    Chat.sender_role == Sender_Role_Enum.ASSISTANT,
                )
            )
            .order_by(Chat.created_at.desc(), Chat.id.desc())
        ).first()

        last_message = get_last_message(session=session, chat=chat)
        last_chats.append(
            {
                "chat_session": chat.serialize(),
                "last_message": (
                    last_message.to_last_message() if last_message else None
                ),
                "unread_message_count": unread_message_count,
                "unread_assistant_message": (
                    True if unread_assistant_message else False
                ),
            }
        )

    return {
        "total_chats": total_chats,
        "chats": last_chats,
        "limit": limit,
        "offset": offset,
    }


@router.get("/chat-details/{client_id}")
async def get_chat_details_by_client_id(
    client_id: int,
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)

    chat_session = session.exec(
        select(Chat_Session)
        .where(Chat_Session.client_id == client_id)
        .where(Chat_Session.user_id == user.id)
    ).first()

    if not chat_session:
        raise HTTPException(
            status_code=404,
            detail="No chat session found for this client and user",
        )

    messages = session.exec(
        select(Chat)
        .where(Chat.chat_session_id == chat_session.id)
        .order_by(Chat.created_at.asc(), Chat.id.asc())
    ).all()

    return {
        "client_id": client_id,
        "chat_session": chat_session.serialize(),
        "messages": [m.serialize() for m in messages],
    }


@router.post("/send-broadcast")
async def send_broadcast(
    request: BroadcastRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)
    contacts = []
    for phone_number in request.contacts:
        phone_number = phonenumbers.parse(phone_number)
        phone_number = (
            f"+{phone_number.country_code}{phone_number.national_number}"
        )
        contacts.append(phone_number)
    # Retrieve clients from the database
    clients = session.exec(
        select(Client).where(Client.phone_number.in_(contacts))
    ).all()
    new_chats = []

    # get message template ID
    content_sid = os.getenv("BROADCAST_TEMPLATE_ID")
    for client in clients:
        client = client.serialize()
        client_name = client.get("name") or client.get("phone_number")

        # generate message to save in database
        message = f"[Broadcast]\n\nHi {client_name},\n{request.message}"

        # Check if chat session exists
        chat_session = session.exec(
            select(Chat_Session).where(
                and_(
                    Chat_Session.user_id == user.id,
                    Chat_Session.client_id == client.get("id"),
                )
            )
        ).first()

        # Create a new chat session if it does not exist
        if not chat_session:
            chat_session = Chat_Session(
                user_id=user.id,
                client_id=client.get("id"),
                platform=Platform_Enum.WHATSAPP,
            )
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)

        # Add chat history
        new_chat = Chat(
            chat_session_id=chat_session.id,
            message=message,
            sender_role=Sender_Role_Enum.USER_BROADCAST,
            status=Chat_Status_Enum.UNREAD,
            created_at=datetime.now(tz),
        )
        new_chats.append(new_chat)

        if not os.getenv("TESTING"):
            # Broadcast a message with/without template
            clean_line_break_message = request.message.replace("\n", " ")
            if content_sid:
                # Template
                background_tasks.add_task(
                    twilio_client.whatsapp_message_template_create,
                    to=client.get("phone_number"),
                    content_variables={
                        "1": client_name,
                        "2": clean_line_break_message,
                    },
                    content_sid=content_sid,
                )
            else:
                # Without template
                background_tasks.add_task(
                    twilio_client.whatsapp_message_create,
                    to=client.get("phone_number"),
                    body=message,
                )

    # Bulk insert new chat messages
    if new_chats:
        session.add_all(new_chats)
    session.commit()
    session.flush()
    return {"message": "Broadcast message sent to WhatsApp"}


# TODO :: delete this route
@router.get("/test-check-24h-window")
async def test_check_24h_window(
    session: Session = Depends(get_session),
):
    check_24h_window(session=session)
    return {"message": "Check 24hours window"}
