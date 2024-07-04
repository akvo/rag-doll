import os
import json
import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from core.database import get_session
from sqlmodel import Session, text

# from sqlmodel import Session, select
# from core.database import engine
from models.chat import PlatformEnum
from routes import user_routes, chat_routes, twilio_routes, slack_routes
from Akvo_rabbitmq_client import rabbitmq_client
from clients.twilio_client import TwilioClient
from clients.slack_client import SlackBotClient
from core.socketio_config import sio_app, user_chats_callback


RABBITMQ_QUEUE_USER_CHATS = os.getenv('RABBITMQ_QUEUE_USER_CHATS')
RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv('RABBITMQ_QUEUE_USER_CHAT_REPLIES')


twilio_client = TwilioClient()
slackbot_client = SlackBotClient()


async def user_chat_replies_callback(body: str):
    queue_message = json.loads(body)
    conversation_envelope = queue_message.get("conversation_envelope", {})
    platform = conversation_envelope.get("platform")
    if platform == PlatformEnum.WHATSAPP.value:
        await twilio_client.send_whatsapp_message(body=body)
    if platform == PlatformEnum.SLACK.value:
        await slackbot_client.send_message(body=body)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq_client.initialize()
    loop = asyncio.get_running_loop()
    loop.create_task(rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_USER_CHATS,
        routing_key=RABBITMQ_QUEUE_USER_CHATS,
        callback=user_chats_callback
    ))
    loop.create_task(rabbitmq_client.consume(
        queue_name=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
        routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
        callback=user_chat_replies_callback
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
app.include_router(slack_routes.router, tags=["slack"])
app.include_router(twilio_routes.router, tags=["twilio"])


@app.get("/health-check", tags=["dev"])
def read_root(session: Session = Depends(get_session)):
    # Test select 1
    session.exec(text("SELECT 1"))
    return {"Hello": "World"}


app.mount('/', app=sio_app)
