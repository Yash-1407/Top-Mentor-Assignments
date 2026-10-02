"""SQL ingestion layer.

SQLite is used so the assignment can run locally without requiring a separate
database server. The same SQL layer can be replaced with MySQL/PostgreSQL
connection code if required by the existing project.
"""

from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("data/assignment.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def ingest_csv_to_sql(csv_path: str, table_name: str = "housing") -> int:
    """Load the CSV into SQL using a parameterized pandas-to-SQL operation."""
    df = pd.read_csv(csv_path)

    with get_connection() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    return len(df)


def query_data_from_sql(table_name: str = "housing") -> pd.DataFrame:
    """Query the ingested data back from SQL."""
    with get_connection() as conn:
        return pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            conn,
        )
