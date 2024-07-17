from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel, Relationship
from utils.util import sanitize_phone_number


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    phone_number: int = Field(
        sa_column=Column(BigInteger, unique=True),
    )
    login_code: str | None = None
    properties: "User_Properties" = Relationship(back_populates="user")

    def __init__(self, **data):
        super().__init__(**data)
        self.phone_number = sanitize_phone_number(
            phone_number=data.get("phone_number")
        )

    # return phone number in international format
    def __str__(self) -> str:
        return f"+{self.phone_number}"

    # dict user serialize phone number to international format
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "phone_number": str(self),
            "name": self.properties.name if self.properties else None,
        }


class User_Properties(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    name: str = Field(
        sa_column=Column(String, unique=True),
    )
    user: "User" = Relationship(back_populates="properties")
