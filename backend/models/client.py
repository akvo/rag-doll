from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel


class Client(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str | None = Field(
        sa_column=Column(String),
    )
    phone_number: int = Field(sa_column=Column(BigInteger, unique=True))
