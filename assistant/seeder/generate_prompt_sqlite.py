import sqlite3
import pandas as pd

FILENAME = "prompt"
DB_NAME = "assistant"


def main():
    sqlite_db = f"./db/{DB_NAME}.sqlite"
    df = pd.read_csv(f"./sources/{FILENAME}.csv")

    if not len(df):
        print("404 - CSV file is empty")
        return None

    conn = sqlite3.connect(sqlite_db)
    df.to_sql("prompt", conn, if_exists="replace", index=False)
    conn.close()
    print(f"{sqlite_db} generated successfully")


if __name__ == "__main__":
    main()
