from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTableWidget,QTableWidgetItem,QFileDialog,QMessageBox,QHeaderView
from plexai_verify.app.collection_engine import CollectionEngine

class AutonomousWishlistDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Collections & Wishlist autonome")
        self.resize(1050, 700)
        self.engine = CollectionEngine()
        self.items = []
        layout = QVBoxLayout(self)
        title = QLabel("Wishlist intelligente — sans Radarr")
        title.setStyleSheet("font-size:20px;font-weight:800;")
        self.summary = QLabel("Analyse en attente.")
        layout.addWidget(title); layout.addWidget(self.summary)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Priorité","Titre","Année","Collection","Motif","Statut"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 1)
        buttons = QHBoxLayout()
        for label, callback in [("Analyser les collections", self.analyze), ("Exporter CSV", self.export_csv), ("Exporter JSON", self.export_json), ("Fermer", self.accept)]:
            button = QPushButton(label); button.clicked.connect(callback); buttons.addWidget(button)
        layout.addLayout(buttons)
        self.analyze()

    def analyze(self):
        collections, self.items = self.engine.analyze()
        self.engine.persist(self.items)
        ordered = sorted(self.items, key=lambda item: (-item.priority, item.collection, item.title))
        self.table.setRowCount(len(ordered))
        for row, item in enumerate(ordered):
            values = ["★" * item.priority, item.title, str(item.year or ""), item.collection, item.reason, item.status]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
        complete = sum(1 for collection in collections if collection["percent"] == 100)
        self.summary.setText(f"{len(collections)} collections analysées • {complete} complètes • {len(self.items)} films manquants")
        if not collections:
            self.summary.setText("Aucun catalogue chargé. Modifie collection_catalog.json puis relance l’analyse.")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter la wishlist", "wishlist_plexai.csv", "CSV (*.csv)")
        if path:
            self.engine.export_csv(path, self.items)
            QMessageBox.information(self, "Export", "Fichier CSV créé.")

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter la wishlist", "wishlist_plexai.json", "JSON (*.json)")
        if path:
            self.engine.export_json(path, self.items)
            QMessageBox.information(self, "Export", "Fichier JSON créé.")
