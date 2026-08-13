"""
analytics/store.py
Event persistence.

STORAGE PATH
------------
The default used to be /tmp/finsight_events.db. On Railway the container
filesystem is ephemeral: /tmp is wiped on every deploy and every restart, so
events were accepted, indexed, served by /analytics/* — and silently erased,
with no error anywhere to indicate the loss.

The path now comes from FINSIGHT_DB_PATH and should point at a mounted volume
in production (e.g. /data/finsight_events.db). The local default stays under
the repo so a developer machine behaves the same way. If the directory is not
writable the module degrades to a temp path and logs loudly, because analytics
must never take down an endpoint.
"""

import json
import logging
import os
import sqlite3
import tempfile
import threading
import uuid

from .models import AnalyticsEvent

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = os.path.join(
    os.environ.get("FINSIGHT_DATA_DIR", os.path.join(os.getcwd(), ".data")),
    "finsight_events.db",
)

_DB_PATH = os.environ.get("FINSIGHT_DB_PATH", _DEFAULT_DB_PATH)

_init_lock = threading.Lock()
_initialised: set[str] = set()


def _resolve_path() -> str:
    """Return a writable DB path, degrading to a temp file rather than raising."""
    path = _DB_PATH
    directory = os.path.dirname(os.path.abspath(path)) or "."
    try:
        os.makedirs(directory, exist_ok=True)
        return path
    except OSError as exc:
        fallback = os.path.join(tempfile.gettempdir(), "finsight_events.db")
        logger.error(
            "analytics DB directory %s is not writable (%s) — falling back to %s; "
            "events will not survive a restart",
            directory, exc, fallback,
        )
        return fallback


def _conn() -> sqlite3.Connection:
    path = _resolve_path()
    conn = sqlite3.connect(path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn, path)
    return conn


def _ensure_schema(conn: sqlite3.Connection, path: str) -> None:
    """Create tables once per path, not on every insert."""
    if path in _initialised:
        return
    with _init_lock:
        if path in _initialised:
            return
        # WAL keeps concurrent readers from blocking the writer under uvicorn
        # workers; the previous connect-per-call pattern serialised everything.
        conn.execute("PRAGMA journal_mode=WAL")
        _init_db(conn)
        _initialised.add(path)


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
        rows = conn.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY created_at", (session_id,)
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_all_events() -> list[dict]:
    conn = _conn()
    try:
        rows = conn.execute("SELECT * FROM events ORDER BY created_at").fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
