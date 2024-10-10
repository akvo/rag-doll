import os
import sqlite3
import pandas as pd

from seeder.generate_prompt_sqlite import main


db_path = "./db/assistant_test.sqlite"


def test_generate_sqlite():
    main(prefix="_test")
    assert os.path.exists(db_path)

    # Check that the SQLite file contains the correct data
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM prompt", conn)
    conn.close()

    assert len(df) >= 3
    assert "en" in df["language"].tolist()
    assert "fr" in df["language"].tolist()
    assert "sw" in df["language"].tolist()


def query_sqlite_by_lang():
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM prompt WHERE language == 'en'", conn)
    assert len(df) == 1
    assert df["language"].tolist() == ["en"]
    conn.close()


def test_remove_sqlie():
    os.remove(db_path)
    assert os.path.exists(db_path) is False
