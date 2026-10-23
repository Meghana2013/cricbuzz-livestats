"""Central database connection handling (the only place that opens connections)."""
import math
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("DB_PATH", PROJECT_ROOT / "data" / "cricbuzz.db"))


class _StdDev:
    """Sample standard deviation aggregate (SQLite has no built-in STDDEV)."""

    def __init__(self) -> None:
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0

    def step(self, value) -> None:
        if value is None:
            return
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        self.m2 += delta * (value - self.mean)

    def finalize(self):
        return math.sqrt(self.m2 / (self.n - 1)) if self.n > 1 else None


def get_connection() -> sqlite3.Connection:
    """Open a connection with foreign keys on, dict-like rows and STDDEV()."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.create_aggregate("STDDEV", 1, _StdDev)
    return conn


def get_readonly_connection() -> sqlite3.Connection:
    """Open a read-only connection (used for user-typed SQL, so nothing can be changed)."""
    uri = DB_PATH.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_aggregate("STDDEV", 1, _StdDev)
    return conn


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    """Transaction scope: commit on success, rollback on any error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_df(sql: str, params: Sequence = ()) -> pd.DataFrame:
    """Run a SELECT and return the result as a pandas DataFrame."""
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def run_readonly_query(sql: str, params: Sequence = ()) -> pd.DataFrame:
    """Run a single SELECT/WITH statement on a read-only connection."""
    statement = sql.strip().rstrip(";").strip()
    if not statement.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT queries are allowed.")
    if ";" in statement:
        raise ValueError("Only one SQL statement is allowed.")
    conn = get_readonly_connection()
    try:
        return pd.read_sql_query(statement, conn, params=params)
    finally:
        conn.close()
