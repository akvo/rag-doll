import os

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel, Relationship
from models import User


VAPID_PRIVATE_KEY = os.getenv("NEXT_PUBLIC_VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("NEXT_PUBLIC_VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {"sub": "mailto:example@mail.com", "aud": ""}


class Subscription(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    endpoint: str = Field(
        sa_column=Column(String, unique=True, nullable=False)
    )
    keys: str = Field(sa_column=Column(String, nullable=False))
    user_id: int = Field(foreign_key="user.id")

    user: "User" = Relationship()

    def __init__(self, **data):
        super().__init__(**data)
