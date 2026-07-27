from __future__ import annotations

from plexai_verify.app.database import get_connection


def init_dna_tables():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS video_signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL UNIQUE,
            algorithm TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            signature TEXT NOT NULL,
            compact_signature TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(movie_id) REFERENCES movies(id)
        )
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_video_signatures_signature
        ON video_signatures(signature)
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS verification_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            label TEXT,
            value TEXT,
            confidence REAL,
            source TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(movie_id) REFERENCES movies(id)
        )
        """)


def save_signature(movie_id, result):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO video_signatures(
            movie_id, algorithm, sample_count, signature, compact_signature
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(movie_id) DO UPDATE SET
            algorithm=excluded.algorithm,
            sample_count=excluded.sample_count,
            signature=excluded.signature,
            compact_signature=excluded.compact_signature,
            updated=CURRENT_TIMESTAMP
        """, (
            movie_id,
            result.algorithm,
            result.sample_count,
            result.signature,
            result.compact_signature,
        ))
        conn.execute("""
        UPDATE movies
        SET video_dna=?, analysis_state='dna_ok',
            last_error=NULL, updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (result.compact_signature, movie_id))


def find_exact_matches(movie_id, signature):
    with get_connection() as conn:
        return conn.execute("""
        SELECT m.*
        FROM video_signatures s
        JOIN movies m ON m.id=s.movie_id
        WHERE s.signature=? AND s.movie_id<>?
        ORDER BY m.filename COLLATE NOCASE
        """, (signature, movie_id)).fetchall()


def get_signature(movie_id):
    with get_connection() as conn:
        return conn.execute("""
        SELECT * FROM video_signatures WHERE movie_id=?
        """, (movie_id,)).fetchone()
