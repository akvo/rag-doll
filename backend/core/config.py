from fastapi import FastAPI

# from sqlmodel import Session, select
# from core.database import engine
# from models import User
from routes import user_routes, chat_routes
import asyncio
from utils.rabbitmq_client import rabbitmq_client


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

app.include_router(user_routes.router, tags=["auth"])
app.include_router(chat_routes.router, tags=["chat"])


@app.on_event("startup")
async def startup_event():
    await rabbitmq_client.initialize()
    loop = asyncio.get_running_loop()
    loop.create_task(rabbitmq_client.consume_user_chats())
    loop.create_task(rabbitmq_client.consume_user_chat_replies())
    loop.create_task(rabbitmq_client.consume_chat_history())
    loop.create_task(rabbitmq_client.consume_twiliobot())


@app.post("/test-rabbitmq-send-message", tags=["dev"])
async def send_message(message: str):
    await rabbitmq_client.producer(body=message)
    return {"status": "Message sent"}


@app.post("/test-rabbitmq-send-magic-link", tags=["dev"])
async def send_magic_link(message: str):
    await rabbitmq_client.send_magic_link(body=message)
    return {"status": "Message sent"}


@app.get("/health-check", tags=["dev"])
def read_root():
    return {"Hello": "World"}
