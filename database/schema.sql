-- Warren SQLite Schema

CREATE TABLE IF NOT EXISTS positions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker      TEXT NOT NULL,
    name        TEXT,
    quantity    REAL,
    cost_basis  REAL,
    sector      TEXT,
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cache (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    fetched_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name   TEXT NOT NULL,
    ticker      TEXT,
    status      TEXT,
    latency_ms  INTEGER,
    called_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scores (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker           TEXT NOT NULL,
    score            REAL,
    signal           TEXT,
    fundamentals     REAL,
    earnings         REAL,
    news_sentiment   REAL,
    smart_money      REAL,
    technicals       REAL,
    scored_at        TEXT DEFAULT (datetime('now'))
);
