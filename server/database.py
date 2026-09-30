import os
import sqlite3
from pathlib import Path

from fastapi import Request


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "secbank.db"


def configured_db_path() -> Path:
    value = os.environ.get("SECBANK_DB_PATH")
    return Path(value).resolve() if value else DEFAULT_DB_PATH


def get_db_path(request: Request) -> Path:
    return request.app.state.db_path


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(users)")
        }

        if "failed_attempts" not in columns:
            connection.execute(
                """
                ALTER TABLE users
                ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0
                """
            )

        if "locked_until" not in columns:
            connection.execute(
                """
                ALTER TABLE users
                ADD COLUMN locked_until INTEGER NOT NULL DEFAULT 0
                """
            )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_user
            ON sessions(user_id)
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_nonces (
                nonce TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                seen_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )