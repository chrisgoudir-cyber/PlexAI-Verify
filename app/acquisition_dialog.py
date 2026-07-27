from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)

from core.acquisition.models import MissingMovie
from core.acquisition.service import AcquisitionService

class AcquisitionDialog(QDialog):
    def __init__(self, missing_movies: list[MissingMovie], parent=None) -> None:
        super().__init__(parent)
        self.movies = missing_movies
        self.service = AcquisitionService()
        self.setWindowTitle("Centre d'acquisition — PlexAI Verify")
        self.resize(1000, 650)
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("🎬 Centre d'acquisition")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Films absents de vos collections. PlexAI Verify ne télécharge rien directement : "
            "il crée une Wishlist, ouvre une recherche autorisée ou transmet la demande à Radarr."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Film", "Année", "Collection", "État", "Identifiant"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.wishlist_btn = QPushButton("＋ Ajouter à la Wishlist")
        self.web_btn = QPushButton("🔎 Rechercher sur le Web")
        self.radarr_btn = QPushButton("Envoyer à Radarr")
        self.test_btn = QPushButton("Tester Radarr")

        self.wishlist_btn.clicked.connect(self._add_wishlist)
        self.web_btn.clicked.connect(self._open_web)
        self.radarr_btn.clicked.connect(self._send_radarr)
        self.test_btn.clicked.connect(self._test_radarr)

        for button in (self.wishlist_btn, self.web_btn, self.radarr_btn, self.test_btn):
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def _populate(self) -> None:
        self.table.setRowCount(len(self.movies))
        for row, movie in enumerate(self.movies):
            values = [
                movie.title,
                str(movie.year or ""),
                movie.collection,
                "Manquant",
                str(movie.external_id or ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (1, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, column, item)

    def _selected_movie(self) -> MissingMovie | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection", "Sélectionnez d'abord un film.")
            return None
        return self.movies[row]

    def _show_result(self, result) -> None:
        if result.success:
            QMessageBox.information(self, result.provider, result.message)
        else:
            QMessageBox.warning(self, result.provider, result.message)

    def _add_wishlist(self) -> None:
        if movie := self._selected_movie():
            self._show_result(self.service.add_to_wishlist(movie))

    def _open_web(self) -> None:
        if movie := self._selected_movie():
            self._show_result(self.service.open_web_search(movie))

    def _send_radarr(self) -> None:
        movie = self._selected_movie()
        if not movie:
            return
        answer = QMessageBox.question(
            self,
            "Confirmation Radarr",
            f"Ajouter « {movie.display_title} » à Radarr ?",
        )
        if answer == QMessageBox.Yes:
            self._show_result(self.service.send_to_radarr(movie))

    def _test_radarr(self) -> None:
        try:
            result = self.service.radarr_client().ping()
        except Exception as exc:
            QMessageBox.warning(self, "Radarr", str(exc))
            return
        self._show_result(result)
