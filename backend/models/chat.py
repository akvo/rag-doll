import enum
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, func
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from models import Client, User


tz = timezone.utc


class Sender_Role_Enum(enum.Enum):
    USER = "user"
    CLIENT = "client"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Platform_Enum(enum.Enum):
    WHATSAPP = "WHATSAPP"
    SLACK = "SLACK"


class Chat_Session(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    client_id: Optional[int] = Field(
        default=None, foreign_key="client.id", nullable=False
    )
    last_read: datetime = Field(
        sa_column=Column(
            DateTime(),
            server_default=func.now(),
            nullable=False,
        ),
        default_factory=lambda: datetime.now(tz),
    )
    client: "Client" = Relationship()
    user: "User" = Relationship()

    def __init__(self, **data):
        super().__init__(**data)

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "name": (
                self.client.properties.name if self.client.properties else None
            ),
            "phone_number": (
                f"+{self.client.phone_number}" if self.client else None
            ),
            "last_read": self.last_read,
        }


class Chat(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="chat_session.id")
    message: str
    sender_role: Sender_Role_Enum = Field(
        sa_column=Column(Enum(Sender_Role_Enum), nullable=False)
    )
    status: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(),
            server_default=func.now(),
            nullable=False,
        ),
        default_factory=lambda: datetime.now(tz),
    )

    media: list["Chat_Media"] = Relationship(back_populates="chat")

    def __init__(self, **data):
        # Remove created_at if it's in the input data
        data.pop("created_at", None)
        super().__init__(**data)

    def serialize(self) -> dict:
        media = []
        if self.media:
            media = [md.simplify() for md in self.media]
        return {
            "id": self.id,
            "chat_session_id": self.chat_session_id,
            "message": self.message,
            "sender_role": self.sender_role.value,
            "created_at": self.created_at,
            "media": media,
        }

    def to_last_message(self) -> dict:
        media = None
        if self.media:
            media = self.media[-1]
            media = media.simplify()
        return {
            "id": self.id,
            "chat_session_id": self.chat_session_id,
            "message": self.message,
            "sender_role": self.sender_role.value,
            "created_at": self.created_at,
            "media": media,
        }


class Chat_Media(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chat.id")
    url: str
    type: str

    chat: Optional[Chat] = Relationship(back_populates="media")

    def simplify(self) -> dict:
        return {
            "url": self.url,
            "type": self.type,
        }
