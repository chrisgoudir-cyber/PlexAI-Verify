from PySide6.QtCore import QObject, Signal, QThread

from plexai_verify.app.video_dna import build_file_dna
from plexai_verify.app.dna_repository import save_signature, find_exact_matches
from plexai_verify.app.database import get_connection


class DNAWorker(QObject):
    progress = Signal(int)
    log = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, movies, sample_count=24):
        super().__init__()
        self.movies = movies
        self.sample_count = sample_count

    def run(self):
        total = max(1, len(self.movies))
        try:
            for index, movie in enumerate(self.movies, start=1):
                if QThread.currentThread().isInterruptionRequested():
                    self.log.emit("Analyse Video DNA interrompue.")
                    break

                try:
                    result = build_file_dna(
                        movie["filepath"],
                        self.sample_count,
                    )
                    save_signature(movie["id"], result)
                    matches = find_exact_matches(
                        movie["id"],
                        result.signature,
                    )

                    if matches:
                        group = f"DNA-{result.signature[:12]}"
                        with get_connection() as conn:
                            ids = [movie["id"]] + [row["id"] for row in matches]
                            for movie_id in ids:
                                conn.execute("""
                                UPDATE movies
                                SET duplicate_group=?, duplicate_score=1.0,
                                    updated=CURRENT_TIMESTAMP
                                WHERE id=?
                                """, (group, movie_id))
                        self.log.emit(
                            f"Doublon exact détecté : {movie['filename']}"
                        )
                    else:
                        self.log.emit(
                            f"Empreinte créée : {movie['filename']}"
                        )
                except Exception as exc:
                    with get_connection() as conn:
                        conn.execute("""
                        UPDATE movies
                        SET last_error=?, analysis_state='dna_error',
                            updated=CURRENT_TIMESTAMP
                        WHERE id=?
                        """, (f"Video DNA : {exc}", movie["id"]))
                    self.error.emit(
                        f"{movie['filename']} : {exc}"
                    )

                self.progress.emit(round(index / total * 100))
        finally:
            self.finished.emit()
