"""Durable per-user conversation history for the Streamlit UI."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).resolve(
).parents[1] / "data" / "chat_history.sqlite3"


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(_DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_history (
            user_id TEXT PRIMARY KEY,
            history_json TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


def load_history(user_id: str | None) -> list[dict[str, Any]]:
    """Load saved exchanges for one authenticated user."""
    if not user_id:
        return []
    with _connect() as connection:
        row = connection.execute(
            "SELECT history_json FROM conversation_history WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return []
    try:
        value = json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def save_history(user_id: str | None, history: list[dict[str, Any]]) -> None:
    """Replace one user's saved history atomically."""
    if not user_id:
        return
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO conversation_history (user_id, history_json)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                history_json = excluded.history_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, json.dumps(history, ensure_ascii=False)),
        )
