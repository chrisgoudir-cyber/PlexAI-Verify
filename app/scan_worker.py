from PySide6.QtCore import QObject, Signal

from app.database import save_movies
from app.scanner import scan_movies


class ScanWorker(QObject):
    progress = Signal(int, int)
    movieFound = Signal(str)
    log = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, folder):
        super().__init__()
        self.folder = folder

    def run(self):
        try:
            movies = scan_movies(self.folder)
            total = len(movies)

            self.log.emit(f"{total} films trouvés.")

            for index, movie in enumerate(movies, start=1):
                self.movieFound.emit(movie["filename"])
                self.progress.emit(index, total)

                if index % 100 == 0:
                    self.log.emit(
                        f"{index} films affichés..."
                    )

            self.log.emit(
                "Enregistrement dans SQLite..."
            )

            save_movies(movies)

            self.log.emit(
                "Base SQLite mise à jour."
            )

        except Exception as exc:
            self.error.emit(str(exc))

        finally:
            self.finished.emit()