import os
import sqlite3
from pathlib import Path

DB_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "catkit"
DB_PATH = DB_DIR / "tasks.db"

TASKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL DEFAULT '',
    dri         TEXT NOT NULL DEFAULT '',
    start_at    TEXT,
    due_at      TEXT,
    priority    INTEGER NOT NULL DEFAULT 1,
    status      TEXT NOT NULL DEFAULT 'todo',
    remind_at   TEXT,
    reminded    INTEGER NOT NULL DEFAULT 0,
    start_remind_at  TEXT,
    start_reminded   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""


def connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(TASKS_SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
        for name, ddl in (
            ("category", "TEXT NOT NULL DEFAULT ''"),
            ("dri", "TEXT NOT NULL DEFAULT ''"),
            ("start_at", "TEXT"),
            ("start_remind_at", "TEXT"),
            ("start_reminded", "INTEGER NOT NULL DEFAULT 0"),
        ):
            if name not in columns:
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {name} {ddl}")
