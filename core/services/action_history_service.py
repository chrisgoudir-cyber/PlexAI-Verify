from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.database import get_connection


class ActionHistoryService:
    def start(self, action_type: str, label: str, item_count: int = 0, *, reversible: bool = False, metadata: dict[str, Any] | None = None) -> int:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO action_history(action_type, label, item_count, reversible, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (action_type, label, int(item_count), int(reversible), json.dumps(metadata or {}, ensure_ascii=False)),
            )
            return int(cur.lastrowid)

    def add_item(self, action_id: int, *, movie_id: int | None, item_type: str, status: str, old_value: str = "", new_value: str = "", confidence: float | None = None, message: str = "", metadata: dict[str, Any] | None = None) -> int:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO action_history_items(
                    action_id, movie_id, item_type, status, old_value, new_value,
                    confidence, message, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (action_id, movie_id, item_type, status, old_value, new_value, confidence, message, json.dumps(metadata or {}, ensure_ascii=False)),
            )
            return int(cur.lastrowid)

    def finish(self, action_id: int, *, status: str, success_count: int = 0, blocked_count: int = 0, error_count: int = 0) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE action_history
                SET status=?, success_count=?, blocked_count=?, error_count=?, finished=?
                WHERE id=?
                """,
                (status, success_count, blocked_count, error_count, datetime.now().isoformat(timespec="seconds"), action_id),
            )

    def list_actions(self, limit: int = 200):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM action_history ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()

    def list_items(self, action_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM action_history_items WHERE action_id=? ORDER BY id",
                (int(action_id),),
            ).fetchall()
