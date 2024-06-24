import re

from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    phone_number: int = Field(
        sa_column=Column(BigInteger, unique=True),
    )
    login_code: str | None = None

    def __init__(self, **data):
        super().__init__(**data)
        self.phone_number = self._sanitize_phone_number(
            data.get('phone_number'))

    def _sanitize_phone_number(self, phone_number):
        if isinstance(phone_number, int):
            return phone_number
        if not re.match(r'^\+\d+$', phone_number):
            raise ValueError("Phone number contains invalid characters")
        phone_number_digits = re.sub(r'\D', '', phone_number)
        return int(phone_number_digits)

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
