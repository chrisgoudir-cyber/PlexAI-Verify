import sqlite3
from pathlib import Path

DB_PATH = Path("data/plexai.db")


def init_database():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL UNIQUE,
            filesize INTEGER
        )
    """)

    conn.commit()
    conn.close()


def clear_movies():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM movies")
    conn.commit()
    conn.close()


def insert_movie(filename, filepath, filesize):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO movies
        (filename, filepath, filesize)
        VALUES (?, ?, ?)
    """, (filename, filepath, filesize))

    conn.commit()
    conn.close()


def count_movies():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM movies")

    total = cur.fetchone()[0]

    conn.close()

    return total
