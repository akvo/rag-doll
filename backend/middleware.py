from fastapi import HTTPException, status
from utils.jwt_handler import verify_jwt_token
from sqlmodel import Session, select
from models import User
from pydantic import BaseModel
from typing import Optional


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class TokenData(BaseModel):
    id: Optional[int] = None


def verify_token(auth):
    token = auth.credentials
    if not token:
        raise credentials_exception
    return verify_jwt_token(token)


def verify_user(session: Session, authenticated):
    authenticated = verify_token(authenticated)
    user_id: str = authenticated.get("uid")
    if user_id is None:
        raise credentials_exception
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise credentials_exception
    return user
