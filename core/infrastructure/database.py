import sqlite3
from pathlib import Path
from contextlib import contextmanager
SCHEMA="""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS movies(id INTEGER PRIMARY KEY AUTOINCREMENT,path TEXT UNIQUE,title TEXT DEFAULT '',year INTEGER,collection_name TEXT DEFAULT '',quality_score INTEGER DEFAULT 0,ai_confidence REAL DEFAULT 0,status TEXT DEFAULT 'unknown',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS issues(id INTEGER PRIMARY KEY AUTOINCREMENT,movie_id INTEGER,category TEXT,severity TEXT DEFAULT 'warning',message TEXT,resolved INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS maintenance_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,started_at TEXT DEFAULT CURRENT_TIMESTAMP,finished_at TEXT,status TEXT DEFAULT 'running',summary TEXT DEFAULT '');
"""
class Database:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row
        try: yield c; c.commit()
        finally: c.close()
    def initialize(self):
        with self.connect() as c: c.executescript(SCHEMA)
    def scalar(self,sql,params=()):
        with self.connect() as c:
            r=c.execute(sql,params).fetchone(); return r[0] if r else None
