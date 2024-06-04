import uvicorn
from os import environ
from core.config import app

BACKEND_PORT = environ.get("BACKEND_PORT", 5000)

if __name__ == "__main__":
    uvicorn.run(app)
