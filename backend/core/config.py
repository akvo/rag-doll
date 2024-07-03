import os
import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import Depends
from core.database import get_session
from sqlmodel import Session, text


# from sqlmodel import Session, select
# from core.database import engine
# from models import User
from routes import user_routes, chat_routes, twilio_routes
from Akvo_rabbitmq_client import rabbitmq_client
from clients.twilio_client import TwilioClient


RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv('RABBITMQ_QUEUE_USER_CHAT_REPLIES')
RABBITMQ_QUEUE_TWILIOBOT_REPLIES = os.getenv('RABBITMQ_QUEUE_TWILIOBOT_REPLIES')


twilio_client = TwilioClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq_client.initialize()
    loop = asyncio.get_running_loop()
    loop.create_task(rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_USER_CHATS,
        routing_key=RABBITMQ_QUEUE_USER_CHATS,
    ))
    loop.create_task(rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
        routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
    ))
    loop.create_task(rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_TWILIOBOT_REPLIES,
        routing_key=f"*.{RABBITMQ_QUEUE_TWILIOBOT_REPLIES}",
        callback=twilio_client.send_whatsapp_message
    ))
    yield
    await rabbitmq_client.disconnect()


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
    lifespan=lifespan
)

app.include_router(user_routes.router, tags=["auth"])
app.include_router(chat_routes.router, tags=["chat"])
app.include_router(twilio_routes.router, tags=["twilio"])


@app.get("/health-check", tags=["dev"])
def read_root(session: Session = Depends(get_session)):
    # Test select 1
    session.exec(text("SELECT 1"))
    return {"Hello": "World"}
