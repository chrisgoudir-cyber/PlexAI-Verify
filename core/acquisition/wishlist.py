from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import MissingMovie


class WishlistRepository:
    def __init__(self, db_path: str | Path = "plexai_verify.db") -> None:
        self.db_path = str(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        db = self._connect()

        try:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS acquisition_wishlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    year INTEGER,
                    collection_name TEXT NOT NULL DEFAULT '',
                    external_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'wanted',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(title, year)
                );

                CREATE TABLE IF NOT EXISTS acquisition_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    year INTEGER,
                    provider TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            db.commit()
        finally:
            db.close()

    def add(self, movie: MissingMovie) -> bool:
        db = self._connect()

        try:
            cursor = db.execute(
                """
                INSERT OR IGNORE INTO acquisition_wishlist
                (title, year, collection_name, external_id)
                VALUES (?, ?, ?, ?)
                """,
                (
                    movie.title,
                    movie.year,
                    movie.collection,
                    movie.external_id,
                ),
            )

            db.commit()
            return cursor.rowcount > 0
        finally:
            db.close()

    def remove(self, title: str, year: int | None = None) -> None:
        db = self._connect()

        try:
            db.execute(
                """
                DELETE FROM acquisition_wishlist
                WHERE title = ? AND year IS ?
                """,
                (title, year),
            )
            db.commit()
        finally:
            db.close()

    def list_all(self) -> list[dict]:
        db = self._connect()

        try:
            rows = db.execute(
                """
                SELECT
                    id,
                    title,
                    year,
                    collection_name,
                    external_id,
                    status,
                    created_at
                FROM acquisition_wishlist
                ORDER BY collection_name, year, title
                """
            ).fetchall()

            return [dict(row) for row in rows]
        finally:
            db.close()

    def log(
        self,
        movie: MissingMovie,
        provider: str,
        success: bool,
        message: str,
    ) -> None:
        db = self._connect()

        try:
            db.execute(
                """
                INSERT INTO acquisition_history
                (title, year, provider, success, message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    movie.title,
                    movie.year,
                    provider,
                    int(success),
                    message,
                ),
            )
            db.commit()
        finally:
            db.close()

    def close(self) -> None:
        """
        Conservée pour compatibilité avec les tests et les futurs appels.

        Les connexions SQLite sont déjà fermées après chaque opération.
        """
        return None