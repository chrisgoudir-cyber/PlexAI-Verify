from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton

from core.services.action_history_service import ActionHistoryService


class ActionHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique général des actions")
        self.resize(1100, 650)
        service = ActionHistoryService()
        rows = service.list_actions()

        layout = QVBoxLayout(self)
        title = QLabel("Historique général et traçabilité")
        title.setStyleSheet("font-size:23px;font-weight:800;")
        layout.addWidget(title)
        layout.addWidget(QLabel("Chaque correction et chaque annulation sont enregistrées avec leur résultat."))

        table = QTableWidget(len(rows), 8)
        table.setHorizontalHeaderLabels(["Date", "Action", "État", "Éléments", "Réussis", "Bloqués", "Erreurs", "Réversible"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for r, item in enumerate(rows):
            values = [item["created"], item["label"], item["status"], item["item_count"], item["success_count"], item["blocked_count"], item["error_count"], "Oui" if item["reversible"] else "Non"]
            for c, value in enumerate(values):
                table.setItem(r, c, QTableWidgetItem(str(value)))
        layout.addWidget(table)
        close = QPushButton("Fermer")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
