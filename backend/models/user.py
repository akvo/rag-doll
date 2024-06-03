from sqlmodel import Field, SQLModel


class UserRoles:
    USER = "user"
    CLIENT = "client"


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str
    email: str | None = None
    phone_number: int
    role: str | None = UserRoles.USER
    login_link: str | None = None
