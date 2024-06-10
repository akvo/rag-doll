from fastapi import FastAPI

# from sqlmodel import Session, select
# from core.database import engine
# from models import User
from routes import user_routes, chat_routes
from utils.rabbitmq_client import RabbitMQBackgroundTasks, RabbitMQClient
from datetime import datetime


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
    listener = RabbitMQBackgroundTasks()
    listener.start()


@app.get("/health-check", tags=["dev"])
def read_root():
    # test send to queue
    # TODO :: Remove this
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    RabbitMQClient().producer(body=f"Time: {now}")
    return {"Hello": "World"}
