import sqlite3
from app.paths import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_database():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL UNIQUE,
            folder TEXT, extension TEXT, filesize INTEGER,
            modified_time REAL, quick_signature TEXT,
            duration REAL, width INTEGER, height INTEGER,
            video_codec TEXT, video_bitrate INTEGER,
            audio_codec TEXT, audio_channels INTEGER,
            audio_languages TEXT, subtitle_languages TEXT, hdr TEXT,
            analyzed INTEGER DEFAULT 0, frames_ready INTEGER DEFAULT 0,
            visual_hash TEXT, video_dna TEXT,
            ai_title TEXT, ai_year INTEGER, ai_confidence REAL,
            ai_status TEXT, ai_notes TEXT,
            tmdb_id INTEGER, tmdb_title TEXT, tmdb_original_title TEXT,
            tmdb_year INTEGER, tmdb_score REAL, tmdb_poster TEXT,
            comparison_status TEXT, proposed_filename TEXT,
            comparison_source TEXT, comparison_score REAL, comparison_message TEXT,
            duplicate_group TEXT, duplicate_score REAL,
            quality_flags TEXT, quality_score INTEGER,
            analysis_state TEXT DEFAULT 'pending', last_error TEXT,
            error_code TEXT, error_action TEXT, media_kind TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        existing = {
            r["name"]
            for r in conn.execute("PRAGMA table_info(movies)")
        }
        migrations = {
            "modified_time": "REAL",
            "quick_signature": "TEXT",
            "video_bitrate": "INTEGER",
            "audio_channels": "INTEGER",
            "frames_ready": "INTEGER DEFAULT 0",
            "visual_hash": "TEXT",
            "video_dna": "TEXT",
            "ai_title": "TEXT",
            "ai_year": "INTEGER",
            "ai_confidence": "REAL",
            "ai_status": "TEXT",
            "ai_notes": "TEXT",
            "tmdb_id": "INTEGER",
            "tmdb_title": "TEXT",
            "tmdb_original_title": "TEXT",
            "tmdb_year": "INTEGER",
            "tmdb_score": "REAL",
            "tmdb_poster": "TEXT",
            "comparison_status": "TEXT",
            "proposed_filename": "TEXT",
            "comparison_source": "TEXT",
            "comparison_score": "REAL",
            "comparison_message": "TEXT",
            "duplicate_group": "TEXT",
            "duplicate_score": "REAL",
            "quality_flags": "TEXT",
            "quality_score": "INTEGER",
            "analysis_state": "TEXT DEFAULT 'pending'",
            "last_error": "TEXT",
            "error_code": "TEXT",
            "error_action": "TEXT",
            "media_kind": "TEXT",
            "validation_status": "TEXT",
            "validation_score": "INTEGER",
            "validation_conflicts": "TEXT",
            "auto_correction_allowed": "INTEGER DEFAULT 0",
        }
        for name, definition in migrations.items():
            if name not in existing:
                conn.execute(
                    f"ALTER TABLE movies ADD COLUMN {name} {definition}"
                )

        conn.execute("""
        CREATE TABLE IF NOT EXISTS rename_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            old_path TEXT NOT NULL,
            new_path TEXT NOT NULL,
            score REAL,
            status TEXT NOT NULL DEFAULT 'done',
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_movies_filename ON movies(filename)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_movies_signature ON movies(quick_signature)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_movies_state ON movies(analysis_state)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_movies_comparison ON movies(comparison_status)"
        )


        conn.execute("""
        CREATE TABLE IF NOT EXISTS video_signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL UNIQUE,
            algorithm TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            signature TEXT NOT NULL,
            compact_signature TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_video_signatures_signature
        ON video_signatures(signature)
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS autopilot_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished DATETIME,
            total INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            already_correct INTEGER DEFAULT 0,
            renamed INTEGER DEFAULT 0,
            uncertain INTEGER DEFAULT 0,
            non_movie INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running'
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS autopilot_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            movie_id INTEGER,
            filename TEXT,
            action TEXT,
            confidence REAL,
            message TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS autonomous_wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, year INTEGER,
            collection_name TEXT NOT NULL DEFAULT '', priority INTEGER NOT NULL DEFAULT 3,
            reason TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'missing',
            created DATETIME DEFAULT CURRENT_TIMESTAMP, updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title, year, collection_name)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS verification_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            label TEXT,
            value TEXT,
            confidence REAL,
            source TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            label TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            item_count INTEGER NOT NULL DEFAULT 0,
            success_count INTEGER NOT NULL DEFAULT 0,
            blocked_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            reversible INTEGER NOT NULL DEFAULT 0,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished DATETIME
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS action_history_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id INTEGER NOT NULL,
            movie_id INTEGER,
            item_type TEXT NOT NULL,
            status TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            confidence REAL,
            message TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(action_id) REFERENCES action_history(id) ON DELETE CASCADE
        )
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_action_history_created
        ON action_history(created)
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_action_items_action
        ON action_history_items(action_id)
        """)


def save_movies(movies):
    with get_connection() as conn:
        for m in movies:
            old = conn.execute(
                "SELECT quick_signature FROM movies WHERE filepath=?",
                (m["filepath"],),
            ).fetchone()
            changed = (
                old is not None
                and old["quick_signature"] != m["quick_signature"]
            )
            conn.execute("""
            INSERT INTO movies(
                filename, filepath, folder, extension, filesize,
                modified_time, quick_signature, media_kind
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(filepath) DO UPDATE SET
                filename=excluded.filename,
                folder=excluded.folder,
                extension=excluded.extension,
                filesize=excluded.filesize,
                modified_time=excluded.modified_time,
                quick_signature=excluded.quick_signature,
                media_kind=excluded.media_kind,
                updated=CURRENT_TIMESTAMP
            """, (
                m["filename"], m["filepath"], m["folder"],
                m["extension"], m["filesize"],
                m["modified_time"], m["quick_signature"],
                m.get("media_kind"),
            ))
            if changed:
                conn.execute("""
                UPDATE movies SET
                    duration=NULL,width=NULL,height=NULL,video_codec=NULL,
                    video_bitrate=NULL,audio_codec=NULL,audio_channels=NULL,
                    audio_languages=NULL,subtitle_languages=NULL,hdr=NULL,
                    analyzed=0,frames_ready=0,visual_hash=NULL,video_dna=NULL,
                    ai_title=NULL,ai_year=NULL,ai_confidence=NULL,
                    ai_status=NULL,ai_notes=NULL,
                    tmdb_id=NULL,tmdb_title=NULL,tmdb_original_title=NULL,
                    tmdb_year=NULL,tmdb_score=NULL,tmdb_poster=NULL,
                    comparison_status=NULL,proposed_filename=NULL,
                    comparison_source=NULL,comparison_score=NULL,
                    duplicate_group=NULL,duplicate_score=NULL,
                    quality_flags=NULL,quality_score=NULL,
                    analysis_state='changed',last_error=NULL,
                    error_code=NULL,error_action=NULL
                WHERE filepath=?
                """, (m["filepath"],))


def get_movies(search="", filter_name="Tous"):
    clauses = []
    params = []

    if search:
        clauses.append("""
        (
            filename LIKE ?
            OR COALESCE(ai_title,'') LIKE ?
            OR COALESCE(tmdb_title,'') LIKE ?
            OR COALESCE(video_codec,'') LIKE ?
            OR COALESCE(audio_codec,'') LIKE ?
            OR COALESCE(hdr,'') LIKE ?
            OR COALESCE(audio_languages,'') LIKE ?
            OR COALESCE(subtitle_languages,'') LIKE ?
        )
        """)
        params.extend([f"%{search}%"] * 8)

    filters = {
        "Non analysés": "analyzed=0",
        "Fichiers modifiés": "analysis_state='changed'",
        "Erreurs": "COALESCE(last_error,'')<>''",
        "Sans images": "frames_ready=0",
        "Non vérifiés IA": "COALESCE(ai_status,'')=''",
        "Non comparés TMDb": "COALESCE(tmdb_title,'')=''",
        "Non comparés IA locale": "COALESCE(comparison_source,'')=''",
        "À renommer": "comparison_status IN ('rename','mismatch') AND COALESCE(proposed_filename,'')<>''",
        "Correspondance sûre": "comparison_status='confirmed'",
        "Nom incorrect": "ai_status='mismatch' OR comparison_status='mismatch'",
        "IA incertaine": "ai_status='uncertain'",
        "Doublons": "COALESCE(duplicate_group,'')<>''",
        "Qualité à contrôler": "COALESCE(quality_flags,'')<>''",
        "Score < 70": "COALESCE(quality_score,100)<70",
        "SD / 720p": "COALESCE(height,0)<=720 AND analyzed=1",
        "Sans sous-titres": "COALESCE(subtitle_languages,'')='' AND analyzed=1",
        "HDR": "hdr IN ('HDR10','HLG','Dolby Vision')",
    }
    if filter_name in filters:
        clauses.append(filters[filter_name])

    where = (
        "WHERE " + " AND ".join(f"({x})" for x in clauses)
        if clauses else ""
    )
    with get_connection() as conn:
        return conn.execute(
            f"""
            SELECT * FROM movies
            {where}
            ORDER BY filename COLLATE NOCASE
            """,
            params,
        ).fetchall()


def get_movie(movie_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM movies WHERE id=?",
            (movie_id,),
        ).fetchone()


def update_metadata(movie_id, m):
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            duration=?,width=?,height=?,video_codec=?,video_bitrate=?,
            audio_codec=?,audio_channels=?,audio_languages=?,
            subtitle_languages=?,hdr=?,analyzed=1,
            analysis_state='metadata_ok',last_error=NULL,
            error_code=NULL,error_action=NULL,
            updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            m.get("duration"),m.get("width"),m.get("height"),
            m.get("video_codec"),m.get("video_bitrate"),
            m.get("audio_codec"),m.get("audio_channels"),
            m.get("audio_languages"),m.get("subtitle_languages"),
            m.get("hdr"),movie_id,
        ))


def update_frames(movie_id, visual_hash, video_dna):
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            frames_ready=1,visual_hash=?,video_dna=?,
            analysis_state='dna_ok',last_error=NULL,
            error_code=NULL,error_action=NULL,
            updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (visual_hash,video_dna,movie_id))


def update_ai(movie_id, r):
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            ai_title=?,ai_year=?,ai_confidence=?,ai_status=?,ai_notes=?,
            analysis_state='ai_ok',last_error=NULL,
            error_code=NULL,error_action=NULL,
            updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            r.get("title"),r.get("year"),r.get("confidence"),
            r.get("status"),r.get("notes"),movie_id,
        ))


def update_tmdb(movie_id, r):
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            tmdb_id=?,tmdb_title=?,tmdb_original_title=?,tmdb_year=?,
            tmdb_score=?,tmdb_poster=?,comparison_status=?,
            proposed_filename=?,comparison_source='TMDb',comparison_score=?,
            analysis_state='tmdb_ok',
            last_error=NULL,updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            r.get("tmdb_id"),r.get("title"),r.get("original_title"),
            r.get("year"),r.get("score"),r.get("poster_path"),
            r.get("comparison_status"),r.get("proposed_filename"),
            r.get("score"),movie_id,
        ))



def update_local_comparison(movie_id, result):
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            comparison_source=?,comparison_score=?,comparison_status=?,
            proposed_filename=?,comparison_message=?,
            analysis_state='local_compare_ok',
            last_error=NULL,updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            result.get("comparison_source"),
            result.get("comparison_score"),
            result.get("comparison_status"),
            result.get("proposed_filename"),
            result.get("comparison_message"),
            movie_id,
        ))

def update_audit(movie_id, group, duplicate_score, flags, score):
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            duplicate_group=?,duplicate_score=?,
            quality_flags=?,quality_score=?,
            updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (group,duplicate_score,flags,score,movie_id))


def clear_audit():
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            duplicate_group=NULL,duplicate_score=NULL,
            quality_flags=NULL,quality_score=NULL
        """)


def set_error(movie_id, text, code=None, action=None):
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            analysis_state='error',last_error=?,
            error_code=?,error_action=?,
            updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            str(text)[:1000],
            str(code or "PROCESSING_ERROR")[:100],
            str(action or "Réessayer l’analyse sur ce film.")[:1000],
            movie_id,
        ))


def apply_rename(movie_id, old_path, new_path, score):
    from pathlib import Path
    new = Path(new_path)
    with get_connection() as conn:
        conn.execute("""
        UPDATE movies SET
            filename=?,filepath=?,folder=?,extension=?,
            comparison_status='renamed',
            comparison_source=COALESCE(comparison_source,'IA locale'),
            analysis_state='renamed',
            updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            new.name, str(new), str(new.parent),
            new.suffix.lower(), movie_id,
        ))
        conn.execute("""
        INSERT INTO rename_history(movie_id, old_path, new_path, score)
        VALUES (?, ?, ?, ?)
        """, (movie_id, old_path, new_path, score))


def last_rename():
    with get_connection() as conn:
        return conn.execute("""
        SELECT * FROM rename_history
        WHERE status='done'
        ORDER BY id DESC LIMIT 1
        """).fetchone()


def mark_rename_undone(history_id, movie_id, restored_path):
    from pathlib import Path
    restored = Path(restored_path)
    with get_connection() as conn:
        conn.execute("""
        UPDATE rename_history
        SET status='undone'
        WHERE id=?
        """, (history_id,))
        conn.execute("""
        UPDATE movies SET
            filename=?,filepath=?,folder=?,extension=?,
            comparison_status='confirmed',
            analysis_state='rename_undone',
            updated=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            restored.name, str(restored), str(restored.parent),
            restored.suffix.lower(), movie_id,
        ))


def dashboard_stats():
    with get_connection() as conn:
        r = conn.execute("""
        SELECT
            COUNT(*) total,
            COALESCE(SUM(filesize),0) total_size,
            SUM(analyzed=1) analyzed,
            SUM(COALESCE(ai_status,'')<>'') ai_checked,
            SUM(COALESCE(comparison_status,'')<>'') tmdb_checked,
            SUM(comparison_status IN ('rename','mismatch')) rename_ready,
            SUM(ai_status='mismatch' OR comparison_status='mismatch') mismatches,
            SUM(COALESCE(duplicate_group,'')<>'') duplicates,
            SUM(COALESCE(quality_flags,'')<>'') quality_alerts,
            SUM(COALESCE(last_error,'')<>'') errors,
            AVG(quality_score) avg_score
        FROM movies
        """).fetchone()
        return {
            k: (
                float(r[k])
                if k == "avg_score" and r[k] is not None
                else int(r[k] or 0)
            )
            for k in r.keys()
        }



def create_autopilot_run(total):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO autopilot_runs(total,status) VALUES (?, 'running')",
            (int(total),),
        )
        return int(cursor.lastrowid)


def add_autopilot_event(
    run_id, movie_id, filename, action, confidence, message
):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO autopilot_events(
            run_id,movie_id,filename,action,confidence,message
        )
        VALUES (?,?,?,?,?,?)
        """, (
            run_id, movie_id, filename, action,
            float(confidence or 0), str(message or "")[:1500],
        ))


def finish_autopilot_run(run_id, summary, status="done"):
    with get_connection() as conn:
        conn.execute("""
        UPDATE autopilot_runs SET
            finished=CURRENT_TIMESTAMP,
            verified=?,
            already_correct=?,
            renamed=?,
            uncertain=?,
            non_movie=?,
            errors=?,
            status=?
        WHERE id=?
        """, (
            int(summary.get("verified", 0)),
            int(summary.get("already_correct", 0)),
            int(summary.get("renamed", 0)),
            int(summary.get("uncertain", 0)),
            int(summary.get("non_movie", 0)),
            int(summary.get("errors", 0)),
            status,
            run_id,
        ))


def latest_autopilot_run():
    with get_connection() as conn:
        return conn.execute("""
        SELECT * FROM autopilot_runs
        ORDER BY id DESC
        LIMIT 1
        """).fetchone()
