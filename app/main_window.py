from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.scanner import scan_movies
from app.database import clear_movies, count_movies

MOVIES_FOLDER = r"\\192.168.1.102\Multimedia\Vidéos\Films"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PlexAI Verify")
        self.resize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        self.path = QLabel(MOVIES_FOLDER)
        self.path.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.progress = QProgressBar()

        self.button = QPushButton("Scanner la bibliothèque")
        self.button.clicked.connect(self.scan)

        top = QHBoxLayout()
        top.addWidget(self.button)
        top.addWidget(self.progress)

        self.movies = QListWidget()

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMaximumHeight(180)

        layout.addWidget(QLabel("Bibliothèque Plex"))
        layout.addWidget(self.path)
        layout.addLayout(top)
        layout.addWidget(self.movies)
        layout.addWidget(QLabel("Journal"))
        layout.addWidget(self.logs)

    def log(self, text):
        self.logs.append(text)

    def scan(self):
        self.movies.clear()

        self.log("Analyse en cours...")

        clear_movies()

        files = scan_movies(MOVIES_FOLDER)

        total = len(files)

        self.progress.setMaximum(max(total, 1))

        for i, movie in enumerate(files, start=1):
            self.movies.addItem(movie.name)
            self.progress.setValue(i)

        self.log(f"{count_movies()} films enregistrés dans la base SQLite.")
        