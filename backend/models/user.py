from sqlalchemy import Column, String, BigInteger
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    phone_number: int = Field(
        sa_column=Column(BigInteger, unique=True),
    )
    login_link: str | None = None


class User_Properties(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str = Field(
        sa_column=Column(String, unique=True),
    )
    email: str | None = Field(
        sa_column=Column(String, unique=True),
    )
