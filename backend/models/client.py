from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel


class Client(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    phone_number: int = Field(sa_column=Column(BigInteger, unique=True))


class Client_Properties(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    name: str = Field(
        sa_column=Column(String, unique=True),
    )
