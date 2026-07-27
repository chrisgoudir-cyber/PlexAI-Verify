from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView
)

from plexai_verify.app.database import get_movies, get_movie
from plexai_verify.app.movie_dialog import MovieDialog


def _problem(movie):
    if movie.get("last_error"):
        code = movie.get("error_code") or "PROCESSING_ERROR"
        labels = {
            "ISO_REQUIRES_MOUNT": "ISO à monter",
            "INVALID_MATROSKA": "Fichier MKV invalide",
            "INVALID_MEDIA": "Média illisible",
            "ACCESS_DENIED": "Accès refusé",
            "FILE_MISSING": "Fichier introuvable",
            "TIMEOUT": "Délai dépassé",
        }
        return labels.get(code, "Erreur d’analyse")

    if movie.get("comparison_status") in ("rename", "mismatch"):
        return "Nom à corriger"
    if movie.get("duplicate_group"):
        return "Doublon"
    if movie.get("quality_flags"):
        return "Qualité"
    return "À vérifier"


class IssuesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Centre des problèmes")
        self.resize(1280, 700)

        root = QVBoxLayout(self)
        title = QLabel("Fichiers demandant ton attention")
        title.setStyleSheet("font-size:23px;font-weight:800;")
        root.addWidget(title)

        rows = []
        seen = set()
        for filter_name in (
            "Erreurs",
            "Nom incorrect",
            "À renommer",
            "Doublons",
            "Qualité à contrôler",
        ):
            for row in get_movies("", filter_name):
                movie = dict(row)
                if movie["id"] in seen:
                    continue
                seen.add(movie["id"])
                rows.append(movie)

        self.rows = rows
        self.table = QTableWidget(len(rows), 7)
        self.table.setHorizontalHeaderLabels([
            "Film", "Problème", "Cause",
            "Action conseillée", "Titre IA",
            "Proposition", "Qualité",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        for row_index, movie in enumerate(rows):
            cause = (
                movie.get("last_error")
                or movie.get("comparison_message")
                or movie.get("quality_flags")
                or "Contrôle nécessaire."
            )
            action = (
                movie.get("error_action")
                or (
                    "Simuler le renommage puis vérifier la proposition."
                    if movie.get("comparison_status") in ("rename", "mismatch")
                    else "Ouvrir la fiche pour contrôler ce fichier."
                )
            )

            values = [
                movie.get("filename") or "",
                _problem(movie),
                cause,
                action,
                movie.get("ai_title") or "—",
                movie.get("proposed_filename") or "—",
                str(movie.get("quality_score") if movie.get("quality_score") is not None else "—"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, movie["id"])
                self.table.setItem(row_index, column, item)

        self.table.doubleClicked.connect(self.open_selected)
        root.addWidget(self.table)

        note = QLabel(
            "Astuce : double-clique sur une ligne pour ouvrir la fiche complète."
        )
        root.addWidget(note)

        buttons = QHBoxLayout()
        open_button = QPushButton("Ouvrir la fiche")
        open_button.clicked.connect(self.open_selected)
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(open_button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        root.addLayout(buttons)

    def open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        movie_id = self.table.item(row, 0).data(Qt.UserRole)
        fresh = get_movie(movie_id)
        if fresh:
            MovieDialog(dict(fresh), self).exec()
