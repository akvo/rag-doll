import os
import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from core.database import get_session
from sqlmodel import Session, text

from routes import (
    user_routes,
    chat_routes,
    twilio_routes,
    slack_routes,
    client_routes,
    subscription_routes,
)
from Akvo_rabbitmq_client import rabbitmq_client
from core.socketio_config import (
    sio_app,
    assistant_to_user,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


RABBITMQ_QUEUE_USER_CHAT_REPLIES = os.getenv(
    "RABBITMQ_QUEUE_USER_CHAT_REPLIES"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq_client.initialize()
    loop = asyncio.get_running_loop()

    async def consume_task():
        await rabbitmq_client.consume(
            queue_name=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            routing_key=RABBITMQ_QUEUE_USER_CHAT_REPLIES,
            callback=assistant_to_user,
        )

    consumer_task = loop.create_task(consume_task())

    try:
        yield
    finally:
        consumer_task.cancel()
        await rabbitmq_client.disconnect()


app = FastAPI(
    title="Rag Doll API",
    root_path="/api",
    description="A Retrieval Augmented Generator project.",
    contact={
        "name": "Akvo",
        "url": "https://akvo.org",
        "email": "dev@akvo.org",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

app.include_router(user_routes.router, tags=["auth"])
app.include_router(client_routes.router, tags=["client"])
app.include_router(chat_routes.router, tags=["chat"])
app.include_router(slack_routes.router, tags=["slack"])
app.include_router(twilio_routes.router, tags=["twilio"])
app.include_router(subscription_routes.router, tags=["push notification"])


@app.get("/health-check", tags=["dev"])
def read_root(session: Session = Depends(get_session)):
    # Test database connectivity
    session.exec(text("SELECT 1"))
    return {"status": "ok"}


app.mount("/", app=sio_app)
