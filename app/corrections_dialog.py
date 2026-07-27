from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QPushButton, QMessageBox,
    QTabWidget, QWidget
)

from core.services.correction_service import CorrectionService
from app.action_history_dialog import ActionHistoryDialog


class CorrectionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Corrections sécurisées")
        self.resize(1250, 720)
        self.service = CorrectionService()

        root = QVBoxLayout(self)
        title = QLabel("Corrections prêtes à être appliquées")
        title.setStyleSheet("font-size:23px;font-weight:800;")
        root.addWidget(title)

        note = QLabel(
            "Seules les propositions avec une confiance d’au moins 95 %, "
            "sans conflit de nom et sans changement d’extension peuvent être appliquées."
        )
        note.setWordWrap(True)
        root.addWidget(note)

        tabs = QTabWidget()
        tabs.addTab(self._build_proposals_tab(), "Propositions")
        tabs.addTab(self._build_history_tab(), "Historique")
        root.addWidget(tabs)

        footer = QHBoxLayout()
        general_history = QPushButton("Historique général")
        general_history.clicked.connect(lambda: ActionHistoryDialog(self).exec())
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        footer.addWidget(general_history)
        footer.addStretch()
        footer.addWidget(close_button)
        root.addLayout(footer)

    def _build_proposals_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        proposals = self.service.list_proposals()
        self.proposals = proposals
        self.proposal_table = QTableWidget(len(proposals), 7)
        self.proposal_table.setHorizontalHeaderLabels([
            "Appliquer", "Nom actuel", "Nouveau nom",
            "Confiance", "Niveau", "Raison", "Blocage"
        ])
        self.proposal_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proposal_table.setEditTriggers(QTableWidget.NoEditTriggers)

        header = self.proposal_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)

        for row, proposal in enumerate(proposals):
            check = QTableWidgetItem()
            check.setFlags(
                Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
            )
            check.setCheckState(
                Qt.Checked if proposal.safe else Qt.Unchecked
            )
            check.setData(Qt.UserRole, proposal.movie_id)
            if not proposal.safe:
                check.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.proposal_table.setItem(row, 0, check)

            values = [
                proposal.old_path.split("\\")[-1],
                proposal.new_path.split("\\")[-1],
                f"{proposal.score * 100:.1f} %",
                proposal.confidence_label + (" — prêt" if proposal.safe else " — bloqué"),
                proposal.reason or "—",
                proposal.blocking_reason or "—",
            ]
            for column, value in enumerate(values, start=1):
                self.proposal_table.setItem(
                    row, column, QTableWidgetItem(str(value))
                )

        layout.addWidget(self.proposal_table)

        buttons = QHBoxLayout()
        simulate = QPushButton("Actualiser la simulation")
        simulate.clicked.connect(self.reload_dialog)
        apply_button = QPushButton("Appliquer les corrections cochées")
        apply_button.clicked.connect(self.apply_selected)
        buttons.addWidget(simulate)
        buttons.addStretch()
        buttons.addWidget(apply_button)
        layout.addLayout(buttons)
        return widget

    def _build_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        history = self.service.history()
        self.history_rows = history
        self.history_table = QTableWidget(len(history), 5)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Ancien nom", "Nouveau nom", "État", "Confiance"
        ])
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        for row, item in enumerate(history):
            values = [
                item["created"],
                item["old_path"].split("\\")[-1],
                item["new_path"].split("\\")[-1],
                item["status"],
                f"{float(item['score'] or 0) * 100:.1f} %",
            ]
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setData(Qt.UserRole, item["id"])
                self.history_table.setItem(row, column, cell)

        layout.addWidget(self.history_table)
        undo_button = QPushButton("Annuler l’opération sélectionnée")
        undo_button.clicked.connect(self.undo_selected)
        layout.addWidget(undo_button)
        return widget

    def selected_movie_ids(self):
        ids = []
        for row in range(self.proposal_table.rowCount()):
            item = self.proposal_table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                ids.append(int(item.data(Qt.UserRole)))
        return ids

    def apply_selected(self):
        ids = self.selected_movie_ids()
        if not ids:
            QMessageBox.information(
                self, "Corrections", "Aucune correction cochée."
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirmer les corrections",
            f"Appliquer {len(ids)} renommage(s) sécurisé(s) ?\n\n"
            "Chaque opération sera enregistrée dans l’historique "
            "et pourra être annulée.",
        )
        if answer != QMessageBox.Yes:
            return

        results = self.service.apply(ids)
        done = sum(result.status == "done" for result in results)
        blocked = sum(result.status == "blocked" for result in results)
        errors = sum(result.status == "error" for result in results)

        QMessageBox.information(
            self,
            "Résultat",
            f"{done} correction(s) appliquée(s)\n"
            f"{blocked} bloquée(s)\n"
            f"{errors} erreur(s)",
        )
        self.reload_dialog()

    def undo_selected(self):
        row = self.history_table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Historique", "Sélectionne une opération."
            )
            return

        history_id = int(
            self.history_table.item(row, 0).data(Qt.UserRole)
        )
        answer = QMessageBox.question(
            self,
            "Annuler le renommage",
            "Restaurer le nom précédent ?",
        )
        if answer != QMessageBox.Yes:
            return

        result = self.service.undo(history_id)
        QMessageBox.information(
            self,
            "Historique",
            result.message,
        )
        self.reload_dialog()

    def reload_dialog(self):
        parent = self.parent()
        self.accept()
        CorrectionsDialog(parent).exec()
