from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPBasicCredentials as credentials
from models import Chat
from sqlmodel import Session, select
from middleware import verify_user
from core.database import get_session


router = APIRouter()
security = HTTPBearer()


@router.get("/chats")
async def get_chats(
    session: Session = Depends(get_session),
    auth: credentials = Depends(security),
):
    user = verify_user(session, auth)
    chats = session.exec(select(Chat).where(Chat.user_id == user.id)).all()
    return {"chats": chats}
