from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget
)
from plexai_verify.app.audit_summary import build_audit_summary


class StatCard(QFrame):
    def __init__(self, title, value, subtitle=""):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)

        value_label = QLabel(str(value))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(
            "font-size: 28px; font-weight: 700;"
        )

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 14px; font-weight: 600;"
        )

        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)

        layout.addWidget(value_label)
        layout.addWidget(title_label)
        if subtitle:
            layout.addWidget(subtitle_label)


class AuditDialog(QDialog):
    def __init__(self, movies, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audit intelligent de la bibliothèque")
        self.resize(900, 650)

        summary = build_audit_summary(movies)
        root = QVBoxLayout(self)

        title = QLabel(
            f"Bibliothèque : {summary['total']} films"
        )
        title.setStyleSheet(
            "font-size: 24px; font-weight: 700;"
        )
        root.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        grid = QGridLayout(body)

        cards = [
            ("Conformes", summary["conformes"], "Analyse cohérente"),
            ("Probables", summary["probables"], "Nom vraisemblable"),
            ("À vérifier", summary["a_verifier"], "Contrôle conseillé"),
            ("À renommer", summary["a_renommer"], "Écart nom / contenu"),
            ("Doublons", summary["doublons"], "Groupes détectés"),
            ("Erreurs", summary["erreurs"], "Analyse incomplète"),
            ("Sans audio FR", summary["sans_audio_fr"], "Piste française absente"),
            ("Sans sous-titres", summary["sans_sous_titres"], "Aucun sous-titre détecté"),
            ("Score moyen", f"{summary['qualite_moyenne']} %", "Confiance globale"),
        ]

        for index, (name, value, subtitle) in enumerate(cards):
            grid.addWidget(
                StatCard(name, value, subtitle),
                index // 3,
                index % 3,
            )

        scroll.setWidget(body)
        root.addWidget(scroll)

        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        root.addWidget(close_button)
