import os
import pandas as pd

from db import connect_to_sqlite, DB_PATH, get_stable_prompt
from seeder.generate_prompt_sqlite import main


db_name = "test"


def test_generate_sqlite():
    main(db_name=db_name)
    assert os.path.exists(DB_PATH.format(db_name=db_name))

    # Check that the SQLite file contains the correct data
    conn = connect_to_sqlite(db_name=db_name)
    df = pd.read_sql("SELECT * FROM prompt", conn)
    conn.close()

    assert len(df) > 0
    assert "id" in df.columns
    assert "stable" in df.columns

    # Check that the SQLite file contains the correct data
    conn = connect_to_sqlite(db_name=db_name)
    df = pd.read_sql("SELECT * FROM prompt_detail", conn)
    conn.close()

    assert len(df) > 0
    assert "id" in df.columns
    assert "system_prompt" in df.columns
    assert "rag_prompt" in df.columns
    assert "ragless_prompt" in df.columns
    assert "prompt_id" in df.columns


def test_get_stable_prompt():
    conn = connect_to_sqlite(db_name=db_name)
    df = get_stable_prompt(conn=conn, language="en")
    assert df is not None
    assert df["language"] == "en"
    assert df["stable"] == 1
    assert "system_prompt" in df
    assert "rag_prompt" in df
    assert "ragless_prompt" in df
    conn.close()


def test_get_stable_if_more_than_one_stable_prompt_for_a_given_language():
    conn = connect_to_sqlite(db_name=db_name)
    cursor = conn.cursor()
    # add more prompt into db
    cursor.execute(
        """
        INSERT INTO prompt_detail (
            id, language,
            system_prompt, rag_prompt, ragless_prompt,
            prompt_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            1000,
            "en",
            "Second system prompt",
            "Second rag prompt",
            "Second ragless prompt",
            1,
        ),
    )
    conn.commit()
    df = get_stable_prompt(conn=conn, language="en")
    assert df["language"] == "en"
    assert df["stable"] == 1
    assert df["system_prompt"] == "Second system prompt"
    assert df["rag_prompt"] == "Second rag prompt"
    assert df["ragless_prompt"] == "Second ragless prompt"
    conn.close()


def test_remove_sqlite():
    os.remove(DB_PATH.format(db_name=db_name))
    assert os.path.exists(DB_PATH.format(db_name=db_name)) is False
