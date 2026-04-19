import json
import sqlite3
import uuid
from .models import AnalyticsEvent

_DB_PATH = "/tmp/finsight_events.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            event_name TEXT NOT NULL,
            properties TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_event_name ON events (event_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON events (session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON events (created_at)")
    conn.commit()


def insert_event(event: AnalyticsEvent) -> None:
    conn = _conn()
    try:
        _init_db(conn)
        conn.execute(
            "INSERT INTO events (id, user_id, session_id, event_name, properties, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                event.user_id,
                event.session_id,
                event.event_name,
                json.dumps(event.properties),
                event.timestamp,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_events(session_id: str) -> list[dict]:
    conn = _conn()
    try:
        _init_db(conn)
        rows = conn.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY created_at", (session_id,)
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_all_events() -> list[dict]:
    conn = _conn()
    try:
        _init_db(conn)
        rows = conn.execute("SELECT * FROM events ORDER BY created_at").fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
