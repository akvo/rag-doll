from sqlalchemy import Column, String, BigInteger, UniqueConstraint
from sqlmodel import Field, SQLModel, Relationship
from utils.util import sanitize_phone_number


class Client(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    phone_number: int = Field(sa_column=Column(BigInteger, unique=True))
    properties: "Client_Properties" = Relationship(back_populates="client")

    def __init__(self, **data):
        super().__init__(**data)
        self.phone_number = sanitize_phone_number(
            phone_number=data.get("phone_number")
        )

    def __str__(self) -> str:
        return f"+{self.phone_number}"

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "phone_number": str(self),
            "name": self.properties.name if self.properties else None,
        }


class Client_Properties(SQLModel, table=True):
    client_id: int = Field(foreign_key="client.id", primary_key=True)
    name: str = Field(
        sa_column=Column(String),
    )
    client: "Client" = Relationship(back_populates="properties")

    __table_args__ = (
        UniqueConstraint("client_id", "name", name="unique_client_name"),
    )
