import enum
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from .user import User  # Import for type checking only


class MessageStatus(str, enum.Enum):
    sent = "sent"
    read = "read"


class Chat(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    client_id: Optional[int] = Field(default=None, foreign_key="user.id")
    message: str
    status: MessageStatus = Field(default=MessageStatus.sent)
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    user: "User" = Relationship(back_populates="chats")
    client: Optional["User"] = Relationship(back_populates="client_chats")
