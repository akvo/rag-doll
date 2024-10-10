import os
import sqlite3
import pandas as pd

from typing import Optional

FILENAME = "prompt"
DB_NAME = "assistant"


def main(prefix: Optional[str] = ""):
    csv_file = f"./sources/{FILENAME}.csv"
    sqlite_db = f"./db/{DB_NAME}{prefix}.sqlite"

    if not os.path.exists(csv_file):
        print(f"404 - File not found: {csv_file}")
        return None

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

    if df.empty:
        print("404 - CSV file is empty")
        return None

    try:
        conn = sqlite3.connect(sqlite_db)
        df.to_sql("prompt", conn, if_exists="replace", index=False)
        conn.close()
        print(f"{sqlite_db} generated successfully")
    except Exception as e:
        print(f"Error writing to SQLite: {e}")


if __name__ == "__main__":
    main()
