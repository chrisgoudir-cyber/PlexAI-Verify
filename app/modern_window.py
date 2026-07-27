from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QGridLayout, QProgressBar,
    QLineEdit, QComboBox, QScrollArea, QSizePolicy
)

from app.main_window import MainWindow as LegacyMainWindow
from app.application_api import app_api
from app.issues_dialog import IssuesDialog
from app.corrections_dialog import CorrectionsDialog
from app.acquisition_dialog import AcquisitionDialog
from app.autonomous_wishlist_dialog import AutonomousWishlistDialog
from core.acquisition.models import MissingMovie


APP_STYLE = """
QMainWindow, QWidget {
    background: #0f1117;
    color: #e8eaed;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QFrame#Sidebar {
    background: #151923;
    border-right: 1px solid #262b38;
}
QLabel#Brand {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
}
QLabel#Muted {
    color: #9aa0aa;
}
QPushButton#NavButton {
    text-align: left;
    padding: 12px 16px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    color: #c8ccd5;
    font-weight: 600;
}
QPushButton#NavButton:hover {
    background: #232938;
    color: white;
}
QPushButton#NavButton:checked {
    background: #e5a00d;
    color: #111318;
}
QPushButton#PrimaryButton {
    padding: 12px 18px;
    border-radius: 8px;
    border: 0;
    background: #e5a00d;
    color: #111318;
    font-weight: 800;
}
QPushButton#PrimaryButton:hover {
    background: #f2b323;
}
QPushButton#SecondaryButton {
    padding: 11px 17px;
    border-radius: 8px;
    border: 1px solid #3a4151;
    background: #202532;
    color: #f1f3f5;
    font-weight: 700;
}
QPushButton#SecondaryButton:hover {
    background: #2a3141;
}
QFrame#Hero {
    background: #181d28;
    border: 1px solid #2a3040;
    border-radius: 14px;
}
QFrame#StatCard {
    background: #181d28;
    border: 1px solid #2a3040;
    border-radius: 12px;
}
QFrame#IssueCard {
    background: #171b25;
    border: 1px solid #303747;
    border-radius: 10px;
}
QFrame#IssueCard:hover {
    border: 1px solid #e5a00d;
}
QLabel#BigNumber {
    font-size: 28px;
    font-weight: 900;
    color: #ffffff;
}
QLabel#PageTitle {
    font-size: 26px;
    font-weight: 900;
}
QProgressBar {
    min-height: 18px;
    max-height: 18px;
    border: 0;
    border-radius: 9px;
    background: #282e3b;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 9px;
    background: #e5a00d;
}
QLineEdit, QComboBox {
    background: #171b24;
    border: 1px solid #343b4b;
    border-radius: 7px;
    padding: 8px;
    color: #eef0f4;
}
QScrollArea {
    border: 0;
}
"""


class MetricCard(QFrame):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.setObjectName("StatCard")
        self.setMinimumHeight(112)
        layout = QVBoxLayout(self)
        self.value = QLabel("0")
        self.value.setObjectName("BigNumber")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight:700;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("Muted")
        subtitle_label.setWordWrap(True)
        layout.addWidget(self.value)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch()


class IssueCard(QFrame):
    def __init__(self, title: str, description: str, callback):
        super().__init__()
        self.setObjectName("IssueCard")
        self.setCursor(Qt.PointingHandCursor)
        self.callback = callback
        self.setMinimumHeight(98)
        layout = QVBoxLayout(self)
        self.value = QLabel("0")
        self.value.setObjectName("BigNumber")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight:800;")
        description_label = QLabel(description)
        description_label.setObjectName("Muted")
        description_label.setWordWrap(True)
        layout.addWidget(self.value)
        layout.addWidget(title_label)
        layout.addWidget(description_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class ModernMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlexAI Verify Enterprise UX 2027")
        self.resize(1500, 920)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(APP_STYLE)

        self.legacy = LegacyMainWindow()
        legacy_widget = self.legacy.takeCentralWidget()
        legacy_widget.setParent(None)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        self.home_page = self._build_home_page()
        self.library_page = self._build_library_page(legacy_widget)
        self.problems_page = self._build_problems_page()
        self.corrections_page = self._build_corrections_page()
        self.acquisition_page = self._build_acquisition_page()
        self.settings_page = self._build_settings_page()

        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.library_page)
        self.pages.addWidget(self.problems_page)
        self.pages.addWidget(self.corrections_page)
        self.pages.addWidget(self.acquisition_page)
        self.pages.addWidget(self.settings_page)

        self.nav_buttons[0].setChecked(True)
        self.pages.setCurrentIndex(0)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_dashboard)
        self.refresh_timer.start(2500)
        self.refresh_dashboard()

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(225)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(8)

        brand = QLabel("PlexAI Verify")
        brand.setObjectName("Brand")
        version = QLabel("Enterprise • Sprint 2")
        version.setObjectName("Muted")
        layout.addWidget(brand)
        layout.addWidget(version)
        layout.addSpacing(24)

        entries = [
            ("⌂  Accueil", 0),
            ("▦  Bibliothèque", 1),
            ("⚠  Problèmes", 2),
            ("✓  Corrections", 3),
            ("★  Wishlist", 4),
            ("⚙  Paramètres", 5),
        ]
        self.nav_buttons = []
        for label, page_index in entries:
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, idx=page_index: self.show_page(idx)
            )
            layout.addWidget(button)
            self.nav_buttons.append(button)

        layout.addStretch()

        status = QLabel(
            "Moteur local\nFFmpeg • SQLite • Ollama"
        )
        status.setObjectName("Muted")
        status.setWordWrap(True)
        layout.addWidget(status)
        return sidebar

    def _build_home_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(18)

        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Bonjour Chris")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Voici l’état actuel de ta bibliothèque Plex."
        )
        subtitle.setObjectName("Muted")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        scan_button = QPushButton("Scanner")
        scan_button.setObjectName("SecondaryButton")
        scan_button.clicked.connect(self.start_scan)

        self.all_in_one_button = QPushButton(
            "▶  TOUT VÉRIFIER ET CORRIGER"
        )
        self.all_in_one_button.setObjectName("PrimaryButton")
        self.all_in_one_button.setMinimumHeight(52)
        self.all_in_one_button.setMinimumWidth(300)
        self.all_in_one_button.setToolTip(
            "Scan + métadonnées + images + IA + correction automatique "
            "uniquement à partir de 95 % de confiance"
        )
        self.all_in_one_button.clicked.connect(self.start_all_in_one)

        header_row.addWidget(scan_button)
        header_row.addWidget(self.all_in_one_button)
        layout.addLayout(header_row)

        autopilot_info = QFrame()
        autopilot_info.setObjectName("Hero")
        autopilot_layout = QHBoxLayout(autopilot_info)
        autopilot_layout.setContentsMargins(22, 18, 22, 18)
        autopilot_text = QVBoxLayout()
        autopilot_title = QLabel("Un seul bouton pour toute la bibliothèque")
        autopilot_title.setStyleSheet(
            "font-size:18px;font-weight:850;"
        )
        autopilot_detail = QLabel(
            "Vérifie le fichier, extrait les images, interroge l’IA, "
            "conserve les noms corrects et corrige automatiquement "
            "uniquement si la certitude atteint 95 %."
        )
        autopilot_detail.setObjectName("Muted")
        autopilot_detail.setWordWrap(True)
        autopilot_text.addWidget(autopilot_title)
        autopilot_text.addWidget(autopilot_detail)
        autopilot_layout.addLayout(autopilot_text, 1)
        launch = QPushButton("Lancer le Tout-en-un")
        launch.setObjectName("PrimaryButton")
        launch.clicked.connect(self.start_all_in_one)
        autopilot_layout.addWidget(launch)
        layout.addWidget(autopilot_info)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        self.hero_message = QLabel("Analyse de la bibliothèque…")
        self.hero_message.setStyleSheet(
            "font-size:21px;font-weight:850;"
        )
        self.hero_detail = QLabel("")
        self.hero_detail.setObjectName("Muted")
        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setFormat("%p %")
        hero_layout.addWidget(self.hero_message)
        hero_layout.addWidget(self.hero_detail)
        hero_layout.addSpacing(8)
        hero_layout.addWidget(self.health_bar)
        layout.addWidget(hero)

        metrics = QGridLayout()
        metrics.setSpacing(12)
        self.metric_total = MetricCard("Films", "Bibliothèque indexée")
        self.metric_size = MetricCard("Taille totale", "Espace utilisé")
        self.metric_metadata = MetricCard("Métadonnées", "Fichiers analysés")
        self.metric_ai = MetricCard("Vérifiés IA", "Contenu reconnu")
        for index, card in enumerate([
            self.metric_total,
            self.metric_size,
            self.metric_metadata,
            self.metric_ai,
        ]):
            metrics.addWidget(card, 0, index)
        layout.addLayout(metrics)

        section = QLabel("À traiter")
        section.setStyleSheet("font-size:18px;font-weight:850;")
        layout.addWidget(section)

        issue_grid = QGridLayout()
        issue_grid.setSpacing(12)
        self.issue_errors = IssueCard(
            "Erreurs",
            "Analyse échouée ou fichier illisible",
            self.show_problems,
        )
        self.issue_rename = IssueCard(
            "À renommer",
            "Correction proposée après vérification",
            lambda: self.show_library_filter("À renommer"),
        )
        self.issue_mismatch = IssueCard(
            "Noms incorrects",
            "Titre ou année incohérents",
            lambda: self.show_library_filter("Nom incorrect"),
        )
        self.issue_duplicates = IssueCard(
            "Doublons",
            "Copies exactes ou versions proches",
            lambda: self.show_library_filter("Doublons"),
        )
        self.issue_quality = IssueCard(
            "Qualité",
            "Résolution, bitrate ou pistes à contrôler",
            lambda: self.show_library_filter("Qualité à contrôler"),
        )
        for index, card in enumerate([
            self.issue_errors,
            self.issue_rename,
            self.issue_mismatch,
            self.issue_duplicates,
            self.issue_quality,
        ]):
            issue_grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(issue_grid)

        section2 = QLabel("Actions rapides")
        section2.setStyleSheet("font-size:18px;font-weight:850;")
        layout.addWidget(section2)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions_data = [
            ("Voir les problèmes", self.show_problems),
            ("Créer Video DNA", self.start_video_dna),
            ("Corrections sécurisées", self.open_corrections),
            ("Exporter rapport", self.export_report),
        ]
        for label, callback in actions_data:
            button = QPushButton(label)
            button.setObjectName("SecondaryButton")
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch()

        scroll.setWidget(body)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        return page

    def _build_library_page(self, legacy_widget):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)

        header = QHBoxLayout()
        title = QLabel("Bibliothèque")
        title.setObjectName("PageTitle")
        self.library_hint = QLabel(
            "Double-clique sur un film pour ouvrir sa fiche."
        )
        self.library_hint.setObjectName("Muted")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.library_hint)
        layout.addLayout(header)

        legacy_widget.setStyleSheet("""
            QWidget { background:#11151d; color:#e7e9ee; }
            QFrame { border-color:#303746; }
            QPushButton {
                background:#222836; color:#eef0f4;
                border:1px solid #394153; border-radius:5px; padding:5px;
            }
            QPushButton:hover { border-color:#e5a00d; }
            QLineEdit, QComboBox, QSpinBox {
                background:#181d27; color:#f0f2f5;
                border:1px solid #394153; border-radius:5px; padding:4px;
            }
            QListWidget, QTextEdit {
                background:#131821; color:#e7e9ee;
                border:1px solid #303746;
            }
            QGroupBox { border:1px solid #303746; border-radius:6px; margin-top:8px; }
        """)
        layout.addWidget(legacy_widget, 1)
        return page

    def _build_problems_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 28, 30, 30)
        title = QLabel("Centre des problèmes")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Regroupe les erreurs, renommages, doublons et alertes qualité."
        )
        subtitle.setObjectName("Muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        self.problem_summary = QLabel("")
        self.problem_summary.setStyleSheet(
            "font-size:18px;font-weight:750;"
        )
        layout.addWidget(self.problem_summary)

        open_button = QPushButton("Ouvrir le tableau détaillé")
        open_button.setObjectName("PrimaryButton")
        open_button.setMaximumWidth(260)
        open_button.clicked.connect(
            lambda: IssuesDialog(self).exec()
        )
        layout.addWidget(open_button)
        layout.addStretch()
        return page


    def _build_corrections_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 28, 30, 30)

        title = QLabel("Corrections sécurisées")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Prévisualise, applique et annule les renommages validés."
        )
        subtitle.setObjectName("Muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        self.correction_summary = QLabel("")
        self.correction_summary.setStyleSheet(
            "font-size:18px;font-weight:750;"
        )
        layout.addWidget(self.correction_summary)

        open_button = QPushButton("Ouvrir le centre de corrections")
        open_button.setObjectName("PrimaryButton")
        open_button.setMaximumWidth(320)
        open_button.clicked.connect(
            lambda: CorrectionsDialog(self).exec()
        )
        layout.addWidget(open_button)

        history_button = QPushButton(
            "Voir et annuler les opérations précédentes"
        )
        history_button.setObjectName("SecondaryButton")
        history_button.setMaximumWidth(360)
        history_button.clicked.connect(
            lambda: CorrectionsDialog(self).exec()
        )
        layout.addWidget(history_button)
        layout.addStretch()
        return page

    def _build_acquisition_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(16)
        title = QLabel("Collections & Wishlist autonome")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Détecte les films manquants à partir de ta bibliothèque et d’un catalogue local. Radarr reste totalement optionnel.")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        open_button = QPushButton("ANALYSER MES COLLECTIONS")
        open_button.setObjectName("PrimaryButton")
        open_button.clicked.connect(self.open_acquisition_center)
        info = QFrame()
        info.setObjectName("Hero")
        info_layout = QVBoxLayout(info)
        info_layout.addWidget(QLabel("Fonctions v15"))
        details = QLabel("• Analyse locale des collections\n• Wishlist automatique et priorités\n• Export CSV et JSON\n• Fonctionnement sans Radarr\n• Catalogue personnalisable : collection_catalog.json")
        details.setObjectName("Muted")
        info_layout.addWidget(details)
        layout.addWidget(title); layout.addWidget(subtitle); layout.addWidget(open_button); layout.addWidget(info); layout.addStretch()
        return page

    def open_acquisition_center(self):
        AutonomousWishlistDialog(self).exec()

    def _build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 28, 30, 30)
        title = QLabel("Paramètres")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Les réglages complets restent disponibles dans la vue Bibliothèque."
        )
        subtitle.setObjectName("Muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        button = QPushButton("Ouvrir les paramètres avancés")
        button.setObjectName("PrimaryButton")
        button.setMaximumWidth(300)
        button.clicked.connect(self.open_settings)
        layout.addWidget(button)
        layout.addStretch()
        return page

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        if index == 0:
            self.refresh_dashboard()

    def show_library_filter(self, filter_name):
        self.show_page(1)
        index = self.legacy.filter_combo.findText(filter_name)
        if index >= 0:
            self.legacy.filter_combo.setCurrentIndex(index)
        self.legacy.load_movies()

    def show_problems(self):
        self.show_page(2)
        self.refresh_dashboard()

    def open_settings(self):
        self.show_page(1)
        if hasattr(self.legacy, "settings_group"):
            self.legacy.settings_group.setChecked(True)
            self.legacy.settings_group.setFocus()

    def start_all_in_one(self):
        self.show_page(1)
        self.legacy.start_all_in_one()

    def start_scan(self):
        self.show_page(1)
        self.legacy.start_scan()

    def start_hybrid(self):
        self.show_page(1)
        self.legacy.start_hybrid()

    def start_video_dna(self):
        self.show_page(1)
        self.legacy.start_video_dna()


    def open_corrections(self):
        self.show_page(3)
        CorrectionsDialog(self).exec()
        self.refresh_dashboard()

    def simulate_rename(self):
        self.show_page(1)
        self.legacy.simulate_rename()

    def export_report(self):
        self.legacy.export_audit_report()

    def refresh_dashboard(self):
        dashboard = app_api.library.dashboard()
        stats = dashboard["stats"]
        self.health_bar.setValue(dashboard["health_display"])

        self.metric_total.value.setText(str(stats.total))
        self.metric_size.value.setText(
            f"{stats.total_size / 1_099_511_627_776:.2f} To"
        )
        self.metric_metadata.value.setText(str(stats.analyzed))
        self.metric_ai.value.setText(str(stats.ai_checked))

        self.issue_errors.value.setText(str(stats.errors))
        self.issue_rename.value.setText(str(stats.rename_ready))
        self.issue_mismatch.value.setText(str(stats.mismatches))
        self.issue_duplicates.value.setText(str(stats.duplicates))
        self.issue_quality.value.setText(str(stats.quality_alerts))

        self.hero_message.setText(dashboard["headline"])
        self.hero_detail.setText(dashboard["detail"])
        proposals = app_api.corrections.list_proposals()
        safe_count = sum(item.safe for item in proposals)
        blocked_count = len(proposals) - safe_count
        self.correction_summary.setText(
            f"{safe_count} correction(s) prête(s), "
            f"{blocked_count} bloquée(s) pour contrôle manuel."
        )

        self.problem_summary.setText(
            f"{stats.errors} erreur(s), "
            f"{stats.rename_ready} renommage(s) prêt(s), "
            f"{stats.duplicates} doublon(s), "
            f"{stats.quality_alerts} alerte(s) qualité."
        )

    def closeEvent(self, event):
        try:
            self.legacy.close()
        finally:
            super().closeEvent(event)
