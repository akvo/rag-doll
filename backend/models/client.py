from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel
from utils.util import sanitize_phone_number


class Client(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    phone_number: int = Field(sa_column=Column(BigInteger, unique=True))

    def __init__(self, **data):
        super().__init__(**data)
        self.phone_number = sanitize_phone_number(
            phone_number=data.get('phone_number'))

    def __str__(self) -> str:
        return f"+{self.phone_number}"

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "phone_number": str(self),
        }


class Client_Properties(SQLModel, table=True):
    client_id: int = Field(foreign_key="client.id", primary_key=True)
    name: str = Field(
        sa_column=Column(String, unique=True),
    )
