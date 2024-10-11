import sqlite3

from typing import Optional


DB_NAME = "assistant"
DB_PATH = "./db/{db_name}.sqlite"


def connect_to_sqlite(db_name: Optional[str] = DB_NAME):
    try:
        conn = sqlite3.connect(DB_PATH.format(db_name=db_name))
        return conn
    except Exception as e:
        print(f"Error connecting to SQLite: {e}")
        return None
