from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from models import Chat_Session, Chat, Sender_Role_Enum, Chat_Status_Enum
from sqlmodel import Session, select, func, and_
from middleware import verify_user
from core.database import get_session

router = APIRouter()
security = HTTPBearer()


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

        last_message = session.exec(
            select(Chat)
            .where(Chat.chat_session_id == chat.id)
            .where(
                Chat.sender_role != Sender_Role_Enum.ASSISTANT,
            )
            .order_by(Chat.created_at.desc(), Chat.id.desc())
        ).first()

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
