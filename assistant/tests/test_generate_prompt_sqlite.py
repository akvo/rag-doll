import os
import sqlite3
import pandas as pd

from seeder.generate_prompt_sqlite import main


def test_generate_csv():
    main(prefix="_test")

    db_path = "./db/assistant_test.sqlite"
    assert os.path.exists(db_path)

    # Check that the SQLite file contains the correct data
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM prompt", conn)
    conn.close()

    assert len(df) >= 3
    assert "en" in df["language"].tolist()
    assert "fr" in df["language"].tolist()
    assert "sw" in df["language"].tolist()
    os.remove(db_path)
