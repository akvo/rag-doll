from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from models import Chat_Session, Chat
from sqlmodel import Session, select
from middleware import verify_user
from core.database import get_session


router = APIRouter()
security = HTTPBearer()


@router.get("/chat-list")
async def get_chats(
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)
    chats = session.exec(
        select(Chat_Session)
        .where(
            Chat_Session.user_id == user.id,
        )
        .order_by(Chat_Session.last_read.desc())
    ).all()
    # map chats to last message
    last_chats = []
    for chat in chats:
        last_message = session.exec(
            select(Chat)
            .where(
                Chat.chat_session_id == chat.id,
            )
            .order_by(Chat.created.desc())
        ).first()
        last_chats.append({"chat_session": chat, "last_message": last_message})
    return last_chats
