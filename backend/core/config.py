from fastapi import FastAPI
from sqlmodel import Session, select
from core.database import create_db_and_tables, engine
from models.user import User
from routes import user_routes

app = FastAPI(
    title="Rag Doll API",
    root_path="/api",
    description="This is a very fancy project.",
    contact={
        "name": "Akvo",
        "url": "https://akvo.org",
        "email": "dev@akvo.org",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.include_router(user_routes.router, prefix="/users", tags=["users"])


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        if not users:
            user = User(
                phone_number=1234567890,
                login_link="",
            )
            session.add(user)
            session.commit()


@app.get("/health-check")
def read_root():
    return {"Hello": "World"}
