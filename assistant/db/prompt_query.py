import pandas as pd

from sqlite3 import Connection


def get_stable_prompt(conn: Connection, language: str):
    query = """
        SELECT *
        FROM prompt_detail pd
        LEFT JOIN prompt p
        ON pd.prompt_id == p.id
        WHERE p.stable == 1
        AND pd.language == '{language}'
        ORDER BY pd.id DESC
    """
    query = query.format(language=language)
    df = pd.read_sql_query(query, conn)
    if df.empty:
        return None
    return df.iloc[0]
