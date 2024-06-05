import enum
from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel, Relationship
from .chat import Chat


class UserRoles(enum.Enum):
    USER: str = "USER"
    CLIENT: str = "CLIENT"


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(
        sa_column=Column(String, unique=True),
    )
    email: str | None = Field(
        sa_column=Column(String, unique=True),
    )
    phone_number: int = Field(
        sa_column=Column(BigInteger, unique=True),
    )
    role: UserRoles = UserRoles.USER
    login_link: str | None = None
    device_token: str | None = None
    chats: list[Chat] = Relationship(back_populates="user")
    client_chats: list[Chat] = Relationship(back_populates="client")
