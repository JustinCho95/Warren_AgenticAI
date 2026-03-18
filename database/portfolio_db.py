import sqlite3
import json
import time
from datetime import datetime
from config.settings import DB_PATH, CACHE_TTL_SECONDS


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        sql = f.read()
    with _get_connection() as conn:
        conn.executescript(sql)


def get_cached_result(key: str) -> dict | None:
    """Return cached value if it exists and is within TTL, else None."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT value, fetched_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
    if row is None:
        return None
    fetched_at = datetime.fromisoformat(row["fetched_at"])
    age = (datetime.utcnow() - fetched_at).total_seconds()
    if age > CACHE_TTL_SECONDS:
        return None
    return json.loads(row["value"])


def save_to_cache(key: str, value: dict) -> None:
    """Upsert a result into the cache."""
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO cache (key, value, fetched_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, fetched_at=excluded.fetched_at",
            (key, json.dumps(value), datetime.utcnow().isoformat()),
        )


def log_tool_call(tool_name: str, ticker: str | None, status: str, latency_ms: int) -> None:
    """Append a row to audit_log."""
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO audit_log (tool_name, ticker, status, latency_ms) VALUES (?, ?, ?, ?)",
            (tool_name, ticker, status, latency_ms),
        )


def save_score(
    ticker: str,
    score: float,
    signal: str,
    fundamentals: float,
    earnings: float,
    news_sentiment: float,
    smart_money: float,
    technicals: float,
) -> None:
    """Save a portfolio score for a ticker."""
    with _get_connection() as conn:
        conn.execute(
            """INSERT INTO scores
               (ticker, score, signal, fundamentals, earnings, news_sentiment, smart_money, technicals)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ticker, score, signal, fundamentals, earnings, news_sentiment, smart_money, technicals),
        )
