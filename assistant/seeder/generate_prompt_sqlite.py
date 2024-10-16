import os
import sqlite3
import pandas as pd
import logging

from db import DB_NAME, DB_PATH
from typing import Optional


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILENAME = "prompt"


def main(db_name: Optional[str] = DB_NAME):
    csv_file = f"./sources/{FILENAME}.csv"
    sqlite_db = DB_PATH.format(db_name=db_name)

    if not os.path.exists(csv_file):
        logger.info(f"404 - File not found: {csv_file}")
        return None

    try:
        prompt_detail = pd.read_csv(csv_file)
        prompt_group_df = pd.DataFrame(
            {
                "id": range(1, len(prompt_detail["stable"].unique()) + 1),
                "stable": prompt_detail["stable"].unique(),
            }
        )
        prompt_detail["prompt_id"] = prompt_detail["stable"].map(
            prompt_group_df.set_index("stable")["id"]
        )
        prompt_detail = prompt_detail.drop(columns=["stable"])
    except Exception as e:
        logger.info(f"Error reading CSV: {e}")
        return None

    if prompt_detail.empty or prompt_group_df.empty:
        logger.info("404 - CSV file is empty")
        return None

    try:
        conn = sqlite3.connect(sqlite_db)
        prompt_group_df.to_sql(
            "prompt", conn, if_exists="replace", index=False
        )
        prompt_detail.to_sql(
            "prompt_detail", conn, if_exists="replace", index=False
        )
        conn.close()
        logger.info(f"{sqlite_db} generated successfully")
    except Exception as e:
        logger.info(f"Error writing to SQLite: {e}")


if __name__ == "__main__":
    main()
