from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    phone_number: int = Field(
        sa_column=Column(BigInteger, unique=True),
    )
    login_code: str | None = None

    # return phone number in international format
    def __str__(self) -> str:
        return f"+{self.phone_number}"

    # dict user serialize phone number to international format
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "phone_number": str(self),
            "login_code": self.login_code,
        }


class User_Properties(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    name: str = Field(
        sa_column=Column(String, unique=True),
    )
    email: str | None = Field(
        sa_column=Column(String, unique=True),
    )
