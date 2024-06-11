import enum
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum
from sqlmodel import Field, SQLModel
from typing import Optional

tz = timezone.utc


class Chat_Sender(enum.Enum):
    USER = "user"
    CLIENT = "client"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Chat_Session(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    last_read: datetime | None = Field(
        sa_column=Column(
            DateTime,
            nullable=True,
        ),
        default=None,
    )


class Chat(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="chat_session.id")
    message: str
    sender: Chat_Sender = Field(
        sa_column=Column(Enum(Chat_Sender), nullable=False)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime,
            server_default="now()",
            nullable=False,
        )
    )

    def __init__(self, **data):
        # Remove created_at if it's in the input data
        data.pop("created_at", None)
        super().__init__(**data)
