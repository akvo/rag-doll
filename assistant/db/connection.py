import sqlite3
import logging

from typing import Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DB_NAME = "assistant"
DB_PATH = "./db/{db_name}.sqlite"


def connect_to_sqlite(db_name: Optional[str] = DB_NAME):
    try:
        conn = sqlite3.connect(DB_PATH.format(db_name=db_name))
        return conn
    except Exception as e:
        logger.warning(f"Error connecting to SQLite: {e}")
        return None
