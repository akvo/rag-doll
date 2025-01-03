import os
import asyncio
import logging
import requests

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from core.database import get_session
from sqlmodel import Session, text, select
from models import Chat

from routes import (
    user_routes,
    chat_routes,
    twilio_routes,
    slack_routes,
    client_routes,
    subscription_routes,
    static_routes,
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
app.include_router(static_routes.router, tags=["static file"])


async def check_rabbitmq():
    try:
        await rabbitmq_client.connect(max_retries=1)
        await rabbitmq_client.disconnect()
        return True
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {e}")
        return False


def check_chromadb():
    try:
        host = f"{os.getenv('CHROMADB_HOST')}:{os.getenv('CHROMADB_PORT')}"
        response = requests.get(f"http://{host}/api/v1/heartbeat")
        print(response.status_code)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        return False


def check_database(session: Session):
    try:
        session.exec(text("SELECT 1"))
        session.exec(select(Chat.id)).first()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_service(service_name: str, port: int):
    try:
        response = requests.get(f"http://{service_name}:{port}/health")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"{service_name} check failed: {e}")
        return False


@app.get("/health-check", tags=["dev"])
async def health_check(session: Session = Depends(get_session)):
    services = {
        "rabbitmq": await check_rabbitmq(),
        "chromadb": check_chromadb(),
        "database": check_database(session=session),
        "assistant": check_service("assistant", os.getenv("ASSISTANT_PORT")),
        "eppo-librarian": check_service(
            "eppo-librarian", os.getenv("EPPO_PORT")
        ),
        "backend": True,
    }
    if all(services.values()):
        return {"status": "healthy", "services": services}
    else:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "services": services},
        )


app.mount("/", app=sio_app)
