from pathlib import Path

from PySide6.QtCore import Qt, QThread, QSize, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QGroupBox,
)

from plexai_verify.app.config import load_config, save_config
from plexai_verify.app.database import dashboard_stats, get_movies
from plexai_verify.app.exporter import export_excel
from plexai_verify.app.paths import DATA_DIR
from plexai_verify.app.renamer import undo_last_rename
from plexai_verify.app.diagnostics import run_diagnostics
from plexai_verify.app.audit_dialog import AuditDialog
from plexai_verify.app.report_exporter import export_audit_html
from plexai_verify.app.movie_dialog import MovieDialog
from plexai_verify.app.issues_dialog import IssuesDialog
from plexai_verify.app.dna_worker import DNAWorker
from plexai_verify.app.workers import (
    AIWorker,
    AuditWorker,
    ProfileWorker,
    FramesWorker,
    MetadataWorker,
    ScanWorker,
    TMDbWorker,
    LocalCompareWorker,
    RenameWorker,
    HybridWorker,
    AllInOneWorker,
)


def duration_text(seconds):
    if not seconds:
        return "—"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class StatCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        self.value = QLabel("0")
        self.value.setStyleSheet("font-size:22px;font-weight:700;")
        caption = QLabel(title)
        caption.setStyleSheet("color:#666;")
        layout.addWidget(self.value)
        layout.addWidget(caption)



class ProblemCard(QFrame):
    clicked = Signal(str)

    def __init__(self, title, filter_name, subtitle=""):
        super().__init__()
        self.filter_name = filter_name
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(105)
        self.setStyleSheet(
            "QFrame { border:1px solid #d7dbe2; border-radius:10px; "
            "background:palette(base); } "
            "QFrame:hover { border:2px solid palette(highlight); }"
        )

        layout = QVBoxLayout(self)
        self.value = QLabel("0")
        self.value.setStyleSheet("font-size:28px;font-weight:800;")
        self.title = QLabel(title)
        self.title.setStyleSheet("font-size:14px;font-weight:700;")
        note = QLabel(subtitle)
        note.setWordWrap(True)
        note.setStyleSheet("color:#70757d;")

        layout.addWidget(self.value)
        layout.addWidget(self.title)
        layout.addWidget(note)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.filter_name)
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = load_config()
        self.worker_thread = None
        self.worker = None
        self.current_movies = []

        self.setWindowTitle("PlexAI Verify v6.0 Stabilisée")
        self.resize(1380, 900)

        # Barre d’outils principale : toujours visible, même sur un écran étroit.
        toolbar = QToolBar("Navigation principale", self)
        toolbar.setObjectName("main_toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self.toolbar_scan_action = toolbar.addAction("Scanner")
        self.toolbar_scan_action.triggered.connect(self.start_scan)

        self.toolbar_hybrid_action = toolbar.addAction("Analyse hybride")
        self.toolbar_hybrid_action.triggered.connect(self.start_hybrid)

        toolbar.addSeparator()

        self.toolbar_audit_action = toolbar.addAction("AUDIT")
        self.toolbar_audit_action.setObjectName("audit_intelligent_action")
        self.toolbar_audit_action.triggered.connect(self.show_audit)

        self.toolbar_report_action = toolbar.addAction("RAPPORT")
        self.toolbar_report_action.triggered.connect(self.export_audit_report)

        toolbar.addSeparator()

        self.toolbar_diagnostic_action = toolbar.addAction("Diagnostic")
        self.toolbar_diagnostic_action.triggered.connect(self.show_diagnostics)

        self.toolbar_rename_action = toolbar.addAction("Simuler renommage")
        self.toolbar_rename_action.triggered.connect(self.simulate_rename)

        toolbar.addSeparator()

        self.toolbar_issues_action = toolbar.addAction("PROBLÈMES")
        self.toolbar_issues_action.triggered.connect(self.show_issues_center)

        self.toolbar_dna_action = toolbar.addAction("VIDEO DNA")
        self.toolbar_dna_action.triggered.connect(self.start_video_dna)


        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("PlexAI Verify")
        title.setStyleSheet("font-size:26px;font-weight:700;")


        self.health_title = QLabel("État de la bibliothèque")
        self.health_title.setStyleSheet("font-size:17px;font-weight:700;")

        self.health_message = QLabel(
            "Calcul de l’état de la bibliothèque…"
        )
        self.health_message.setStyleSheet(
            "font-size:20px;font-weight:800;"
        )

        self.health_progress = QProgressBar()
        self.health_progress.setRange(0, 100)
        self.health_progress.setFormat("Santé globale : %p %")
        self.health_progress.setMinimumHeight(28)

        self.health_precision = QLabel("Calcul en cours…")
        self.health_precision.setAlignment(Qt.AlignRight)
        self.health_precision.setStyleSheet("color:#59606b;")

        self.problem_rename = ProblemCard(
            "À renommer",
            "À renommer",
            "Nom différent du contenu reconnu",
        )
        self.problem_mismatch = ProblemCard(
            "Noms incorrects",
            "Nom incorrect",
            "Titre ou année probablement erronés",
        )
        self.problem_duplicates = ProblemCard(
            "Doublons",
            "Doublons",
            "Copies ou encodages très proches",
        )
        self.problem_quality = ProblemCard(
            "Qualité à contrôler",
            "Qualité à contrôler",
            "Bitrate, résolution ou piste à vérifier",
        )
        self.problem_errors = ProblemCard(
            "Erreurs",
            "Erreurs",
            "Fichiers dont l’analyse a échoué",
        )

        for card in (
            self.problem_rename,
            self.problem_mismatch,
            self.problem_duplicates,
            self.problem_quality,
        ):
            card.clicked.connect(self.open_problem_filter)
        self.problem_errors.clicked.connect(
            lambda _name: self.show_issues_center()
        )

        problem_grid = QGridLayout()
        problem_grid.setHorizontalSpacing(10)
        for index, card in enumerate((
            self.problem_rename,
            self.problem_mismatch,
            self.problem_duplicates,
            self.problem_quality,
            self.problem_errors,
        )):
            problem_grid.addWidget(card, 0, index)

        self.quick_scan_button = QPushButton("1. Scanner")
        self.quick_scan_button.setMinimumHeight(42)
        self.quick_scan_button.clicked.connect(self.start_scan)

        self.quick_analyze_button = QPushButton("2. Analyser intelligemment")
        self.quick_analyze_button.setMinimumHeight(42)
        self.quick_analyze_button.clicked.connect(self.start_hybrid)

        self.quick_audit_button = QPushButton("3. Voir les problèmes")
        self.quick_audit_button.setMinimumHeight(42)
        self.quick_audit_button.clicked.connect(self.show_audit)

        self.quick_fix_button = QPushButton("4. Simuler les corrections")
        self.quick_fix_button.setMinimumHeight(42)
        self.quick_fix_button.clicked.connect(self.simulate_rename)

        self.quick_dna_button = QPushButton("5. Créer Video DNA")
        self.quick_dna_button.setMinimumHeight(42)
        self.quick_dna_button.clicked.connect(self.start_video_dna)

        quick_actions = QHBoxLayout()
        quick_actions.addWidget(self.quick_scan_button)
        quick_actions.addWidget(self.quick_analyze_button)
        quick_actions.addWidget(self.quick_audit_button)
        quick_actions.addWidget(self.quick_fix_button)
        quick_actions.addWidget(self.quick_dna_button)

        action_center = QFrame()
        action_center.setObjectName("action_center")
        action_center.setStyleSheet(
            "#action_center { border:1px solid #cfd5de; "
            "border-radius:12px; padding:8px; background:palette(alternate-base); }"
        )
        action_layout = QVBoxLayout(action_center)
        action_layout.addWidget(self.health_title)
        action_layout.addWidget(self.health_message)
        action_layout.addWidget(self.health_progress)
        action_layout.addWidget(self.health_precision)
        action_layout.addLayout(problem_grid)
        action_layout.addLayout(quick_actions)


        self.stat_total = StatCard("Films")
        self.stat_size = StatCard("Taille totale")
        self.stat_analyzed = StatCard("Métadonnées")
        self.stat_ai = StatCard("Vérifiés IA")
        self.stat_duplicates = StatCard("Doublons")
        self.stat_alerts = StatCard("Alertes qualité")

        stats_grid = QGridLayout()
        for index, card in enumerate((
            self.stat_total,
            self.stat_size,
            self.stat_analyzed,
            self.stat_ai,
            self.stat_duplicates,
            self.stat_alerts,
        )):
            stats_grid.addWidget(card, 0, index)

        self.path_edit = QLineEdit(self.config["movies_folder"])
        browse_button = QPushButton("Parcourir")
        browse_button.clicked.connect(self.choose_folder)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_button)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Rechercher : titre, codec, langue, HDR..."
        )
        self.search.textChanged.connect(self.load_movies)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Tous",
            "Non analysés",
            "Fichiers modifiés",
            "Erreurs",
            "Sans images",
            "Non vérifiés IA",
            "Non comparés TMDb",
            "Non comparés IA locale",
            "À renommer",
            "Correspondance sûre",
            "Nom incorrect",
            "IA incertaine",
            "Doublons",
            "Qualité à contrôler",
            "Score < 70",
            "SD / 720p",
            "Sans sous-titres",
            "HDR",
        ])
        self.filter_combo.currentTextChanged.connect(self.load_movies)

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Rapide", "Complet", "Expert"])
        self.profile_combo.setCurrentText(self.config.get("analysis_profile", "Rapide"))
        self.skip_unchanged = QCheckBox("Ignorer les fichiers inchangés")
        self.skip_unchanged.setChecked(bool(self.config.get("skip_unchanged", True)))
        self.profile_button = QPushButton("Lancer le profil")
        self.profile_button.clicked.connect(self.start_profile)
        self.stop_button = QPushButton("Arrêter")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_worker)

        search_row = QHBoxLayout()
        search_row.addWidget(self.search, 3)
        search_row.addWidget(self.filter_combo, 1)

        self.scan_button = QPushButton("Scanner")
        self.scan_button.clicked.connect(self.start_scan)

        self.meta_button = QPushButton("Métadonnées FFprobe")
        self.meta_button.clicked.connect(self.start_metadata)

        self.frames_button = QPushButton("Extraire les images")
        self.frames_button.clicked.connect(self.start_frames)

        self.ai_button = QPushButton("Vérifier par IA locale")
        self.ai_button.clicked.connect(self.start_ai)

        self.hybrid_button = QPushButton("Analyse hybride Express + IA")
        self.hybrid_button.clicked.connect(self.start_hybrid)

        self.diagnostic_button = QPushButton("Diagnostic")
        self.diagnostic_button.clicked.connect(self.show_diagnostics)

        self.audit_button = QPushButton("AUDIT INTELLIGENT")
        self.audit_button.setObjectName("audit_intelligent_button")
        self.audit_button.setMinimumHeight(38)
        self.audit_button.setStyleSheet(
            "QPushButton { font-weight: 700; padding: 8px 16px; "
            "border: 2px solid palette(highlight); border-radius: 6px; }"
        )
        self.audit_button.clicked.connect(self.show_audit)

        self.audit_export_button = QPushButton("Exporter rapport HTML")
        self.audit_export_button.clicked.connect(self.export_audit_report)

        self.local_compare_button = QPushButton("Préparer renommage IA locale")
        self.local_compare_button.clicked.connect(self.start_local_compare)

        self.tmdb_button = QPushButton("Comparer avec TMDb (optionnel)")
        self.tmdb_button.clicked.connect(self.start_tmdb)

        self.simulate_rename_button = QPushButton("Simuler renommage")
        self.simulate_rename_button.clicked.connect(self.simulate_rename)

        self.rename_button = QPushButton("Renommage auto sécurisé")
        self.rename_button.clicked.connect(self.start_rename)

        self.undo_rename_button = QPushButton("Annuler dernier renommage")
        self.undo_rename_button.clicked.connect(self.undo_rename)

        self.duplicates_button = QPushButton("Détecter doublons / qualité")
        self.duplicates_button.clicked.connect(self.start_audit)

        self.export_button = QPushButton("Exporter Excel")
        self.export_button.clicked.connect(self.export_data)

        actions = QHBoxLayout()
        for button in (
            self.scan_button,
            self.meta_button,
            self.frames_button,
            self.ai_button,
            self.hybrid_button,
            self.diagnostic_button,
            self.audit_button,
            self.audit_export_button,
            self.local_compare_button,
            self.tmdb_button,
            self.simulate_rename_button,
            self.rename_button,
            self.undo_rename_button,
            self.duplicates_button,
            self.export_button,
        ):
            actions.addWidget(button)
        actions.addStretch()

        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Profil d’analyse :"))
        profile_row.addWidget(self.profile_combo)
        profile_row.addWidget(self.skip_unchanged)
        profile_row.addWidget(self.profile_button)
        profile_row.addWidget(self.stop_button)
        profile_row.addStretch()

        settings_form = QFormLayout()
        self.ffmpeg_edit = QLineEdit(self.config["ffmpeg_path"])
        self.ffprobe_edit = QLineEdit(self.config["ffprobe_path"])
        self.ollama_url_edit = QLineEdit(self.config["ollama_url"])
        self.ollama_model_edit = QLineEdit(self.config["ollama_model"])
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(3, 12)
        self.frames_spin.setValue(int(self.config["frames_per_movie"]))
        self.tmdb_token_edit = QLineEdit(self.config.get("tmdb_token", ""))
        self.tmdb_token_edit.setEchoMode(QLineEdit.Password)
        self.tmdb_language_edit = QLineEdit(self.config.get("tmdb_language", "fr-FR"))
        self.rename_format_edit = QLineEdit(
            self.config.get("rename_format", "{title} ({year})")
        )
        self.rename_threshold_spin = QSpinBox()
        self.rename_threshold_spin.setRange(75, 100)
        self.rename_threshold_spin.setValue(
            int(self.config.get("rename_threshold", 95))
        )

        settings_form.addRow("FFmpeg :", self.ffmpeg_edit)
        settings_form.addRow("FFprobe :", self.ffprobe_edit)
        settings_form.addRow("Ollama :", self.ollama_url_edit)
        settings_form.addRow("Modèle IA :", self.ollama_model_edit)
        settings_form.addRow("Images par film :", self.frames_spin)
        settings_form.addRow("Clé / jeton TMDb (optionnel) :", self.tmdb_token_edit)
        settings_form.addRow("Langue TMDb :", self.tmdb_language_edit)
        settings_form.addRow("Format renommage :", self.rename_format_edit)
        settings_form.addRow("Seuil renommage (%) :", self.rename_threshold_spin)

        save_settings_button = QPushButton("Enregistrer les paramètres")
        save_settings_button.clicked.connect(self.save_settings)

        self.settings_group = QGroupBox("Paramètres avancés")
        self.settings_group.setCheckable(True)
        self.settings_group.setChecked(False)
        self.settings_group.setStyleSheet(
            "QGroupBox { font-weight:700; margin-top:8px; }"
        )
        settings_group_layout = QVBoxLayout(self.settings_group)
        settings_group_layout.addLayout(settings_form)
        settings_group_layout.addWidget(save_settings_button)

        self.progress = QProgressBar()

        self.movies = QListWidget()
        self.movies.setSelectionMode(QListWidget.ExtendedSelection)
        self.movies.currentItemChanged.connect(self.show_details)
        self.movies.itemDoubleClicked.connect(self.open_movie_card)

        self.details = QTextEdit()
        self.details.setReadOnly(True)

        content = QHBoxLayout()
        content.addWidget(self.movies, 2)
        content.addWidget(self.details, 1)

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMaximumHeight(165)

        layout.addWidget(title)
        layout.addWidget(action_center)
        layout.addLayout(stats_grid)
        layout.addWidget(QLabel("Bibliothèque"))
        layout.addLayout(path_row)
        layout.addLayout(search_row)
        layout.addLayout(actions)
        layout.addLayout(profile_row)
        layout.addWidget(self.settings_group)
        layout.addWidget(self.progress)
        layout.addLayout(content)
        layout.addWidget(QLabel("Journal"))
        layout.addWidget(self.logs)

        self.statusBar().showMessage(f"Données : {DATA_DIR}")
        self.load_movies()



    def show_issues_center(self):
        IssuesDialog(self).exec()
        self.load_movies()

    def open_movie_card(self, item):
        if item is None:
            return
        movie_id = item.data(Qt.UserRole)
        movie = next(
            (
                dict(row)
                for row in self.current_movies
                if row["id"] == movie_id
            ),
            None,
        )
        if movie:
            MovieDialog(movie, self).exec()

    def start_video_dna(self):
        rows = self.selected_rows()
        if not rows:
            QMessageBox.information(
                self,
                "Video DNA",
                "Aucun film sélectionné.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Créer les empreintes Video DNA",
            f"Créer une empreinte locale pour {len(rows)} film(s) ?\n\n"
            "Conseil : commence avec quelques films. "
            "Cette opération lit plusieurs zones de chaque fichier.",
        )
        if answer != QMessageBox.Yes:
            return

        self.run_worker(
            DNAWorker(rows, sample_count=24),
            f"Création Video DNA pour {len(rows)} film(s)...",
        )

    def open_problem_filter(self, filter_name):
        index = self.filter_combo.findText(filter_name)
        if index >= 0:
            self.filter_combo.setCurrentIndex(index)
        self.search.clear()
        self.load_movies()
        self.statusBar().showMessage(
            f"Filtre actif : {filter_name}",
            5000,
        )

    def log(self, text):
        self.logs.append(text)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choisir la bibliothèque",
            self.path_edit.text(),
        )
        if folder:
            self.path_edit.setText(folder)
            self.save_settings()

    def save_settings(self):
        self.config.update({
            "movies_folder": self.path_edit.text().strip(),
            "ffmpeg_path": self.ffmpeg_edit.text().strip(),
            "ffprobe_path": self.ffprobe_edit.text().strip(),
            "ollama_url": self.ollama_url_edit.text().strip(),
            "ollama_model": self.ollama_model_edit.text().strip(),
            "frames_per_movie": self.frames_spin.value(),
            "analysis_profile": self.profile_combo.currentText(),
            "skip_unchanged": self.skip_unchanged.isChecked(),
            "tmdb_token": self.tmdb_token_edit.text().strip(),
            "tmdb_language": self.tmdb_language_edit.text().strip(),
            "rename_format": self.rename_format_edit.text().strip(),
            "rename_threshold": self.rename_threshold_spin.value(),
        })
        save_config(self.config)
        self.statusBar().showMessage("Paramètres enregistrés", 4000)

    def set_busy(self, busy):
        for button in (
            self.scan_button,
            self.meta_button,
            self.frames_button,
            self.ai_button,
            self.hybrid_button,
            self.diagnostic_button,
            self.audit_button,
            self.audit_export_button,
            self.local_compare_button,
            self.tmdb_button,
            self.simulate_rename_button,
            self.rename_button,
            self.undo_rename_button,
            self.duplicates_button,
            self.export_button,
            self.profile_button,
            self.quick_scan_button,
            self.quick_analyze_button,
            self.quick_audit_button,
            self.quick_fix_button,
            self.quick_dna_button,
        ):
            button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        for action in (
            self.toolbar_scan_action,
            self.toolbar_hybrid_action,
            self.toolbar_audit_action,
            self.toolbar_report_action,
            self.toolbar_diagnostic_action,
            self.toolbar_rename_action,
            self.toolbar_issues_action,
            self.toolbar_dna_action,
        ):
            action.setEnabled(not busy)

    def selected_rows(self):
        selected_ids = {
            item.data(Qt.UserRole)
            for item in self.movies.selectedItems()
        }
        if selected_ids:
            return [
                dict(row)
                for row in self.current_movies
                if row["id"] in selected_ids
            ]
        return [dict(row) for row in self.current_movies]

    def all_rows(self):
        return [
            dict(row)
            for row in get_movies("", "Tous")
        ]

    def run_worker(self, worker, start_message):
        if self.worker_thread is not None:
            QMessageBox.information(
                self,
                "Traitement en cours",
                "Attends la fin du traitement actuel.",
            )
            return

        self.save_settings()
        self.set_busy(True)
        self.progress.setValue(0)
        self.log(start_message)

        self.worker_thread = QThread(self)
        self.worker = worker
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.log.connect(self.log)
        self.worker.error.connect(lambda text: self.log(f"Erreur : {text}"))
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.cleanup_worker)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def worker_finished(self):
        self.set_busy(False)
        self.load_movies()
        self.log("Traitement terminé.")

    def cleanup_worker(self):
        self.worker = None
        self.worker_thread = None

    def stop_worker(self):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.log("Arrêt demandé : le fichier en cours sera terminé proprement.")

    def start_profile(self):
        rows = self.all_rows()
        if not rows:
            QMessageBox.information(self, "Information", "Aucun film.")
            return
        profile = self.profile_combo.currentText()
        if profile == "Expert":
            answer = QMessageBox.question(self, "Profil Expert", f"Lancer l’IA locale sur jusqu’à {len(rows)} films ?\nLe traitement peut être très long.")
            if answer != QMessageBox.Yes:
                return
        self.run_worker(
            ProfileWorker(rows, profile, self.ffprobe_edit.text().strip(), self.ffmpeg_edit.text().strip(), self.frames_spin.value(), self.ollama_url_edit.text().strip(), self.ollama_model_edit.text().strip(), self.skip_unchanged.isChecked()),
            f"Profil {profile} lancé sur {len(rows)} film(s)...",
        )

    def start_scan(self):
        folder = self.path_edit.text().strip()
        if not folder:
            QMessageBox.warning(
                self,
                "Erreur",
                "Indique un dossier de films.",
            )
            return

        self.run_worker(
            ScanWorker(folder),
            "Scan de la bibliothèque...",
        )

    def start_metadata(self):
        rows = self.selected_rows()
        if not rows:
            QMessageBox.information(self, "Information", "Aucun film.")
            return

        ffprobe_path = self.ffprobe_edit.text().strip()
        if not Path(ffprobe_path).exists():
            QMessageBox.warning(
                self,
                "FFprobe introuvable",
                ffprobe_path,
            )
            return

        self.run_worker(
            MetadataWorker(rows, ffprobe_path),
            f"Analyse FFprobe de {len(rows)} film(s)...",
        )

    def start_frames(self):
        rows = [
            row for row in self.selected_rows()
            if row.get("duration")
        ]
        if not rows:
            QMessageBox.information(
                self,
                "Métadonnées requises",
                "Analyse d'abord les métadonnées FFprobe.",
            )
            return

        ffmpeg_path = self.ffmpeg_edit.text().strip()
        if not Path(ffmpeg_path).exists():
            QMessageBox.warning(
                self,
                "FFmpeg introuvable",
                ffmpeg_path,
            )
            return

        self.run_worker(
            FramesWorker(
                rows,
                ffmpeg_path,
                self.frames_spin.value(),
            ),
            f"Extraction d'images pour {len(rows)} film(s)...",
        )

    def start_ai(self):
        rows = [
            row for row in self.selected_rows()
            if row.get("duration")
        ]
        if not rows:
            QMessageBox.information(
                self,
                "Métadonnées requises",
                "Analyse d'abord les métadonnées FFprobe.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Analyse IA",
            f"Analyser {len(rows)} film(s) avec Ollama ?\n\n"
            "Commence par sélectionner un seul film pour tester.",
        )
        if answer != QMessageBox.Yes:
            return

        self.run_worker(
            AIWorker(
                rows,
                self.ffmpeg_edit.text().strip(),
                self.frames_spin.value(),
                self.ollama_url_edit.text().strip(),
                self.ollama_model_edit.text().strip(),
            ),
            f"Analyse IA locale de {len(rows)} film(s)...",
        )





    def show_audit(self):
        rows = self.all_rows()
        if not rows:
            QMessageBox.information(
                self, "Audit", "Aucun film à analyser."
            )
            return
        AuditDialog(rows, self).exec()

    def export_audit_report(self):
        rows = self.all_rows()
        if not rows:
            QMessageBox.information(
                self, "Audit", "Aucun film à exporter."
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter le rapport d’audit",
            "PlexAI-Verify-Audit-v3.html",
            "Rapport HTML (*.html)",
        )
        if not path:
            return

        try:
            export_audit_html(rows, path)
            QMessageBox.information(
                self,
                "Audit",
                f"Rapport créé :\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", str(exc))

    def show_diagnostics(self):
        self.save_settings()
        result = run_diagnostics(self.config)
        lines = [
            ("Bibliothèque", result["library"]),
            ("FFmpeg", result["ffmpeg"]),
            ("FFprobe", result["ffprobe"]),
            ("Ollama", result["ollama"]),
            ("Modèle IA", result["model"]),
        ]
        report = "\n".join(
            f"{'🟢' if ok else '🔴'} {name}"
            for name, ok in lines
        )
        report += f"\n\n{result['ollama_message']}"
        QMessageBox.information(self, "Diagnostic PlexAI Verify", report)


    def start_all_in_one(self):
        folder = self.path_edit.text().strip()
        if not folder:
            QMessageBox.warning(
                self,
                "Dossier manquant",
                "Indique le dossier de ta bibliothèque.",
            )
            return

        diagnostics = run_diagnostics({
            **self.config,
            "movies_folder": folder,
            "ffmpeg_path": self.ffmpeg_edit.text().strip(),
            "ffprobe_path": self.ffprobe_edit.text().strip(),
            "ollama_url": self.ollama_url_edit.text().strip(),
            "ollama_model": self.ollama_model_edit.text().strip(),
        })
        missing = []
        if not diagnostics["library"]:
            missing.append("bibliothèque")
        if not diagnostics["ffmpeg"]:
            missing.append("FFmpeg")
        if not diagnostics["ffprobe"]:
            missing.append("FFprobe")
        if not diagnostics["ollama"]:
            missing.append("Ollama")
        if not diagnostics["model"]:
            missing.append("modèle IA")

        if missing:
            QMessageBox.warning(
                self,
                "Tout-en-un indisponible",
                "Éléments manquants : "
                + ", ".join(missing)
                + ".\n\n"
                + diagnostics["ollama_message"],
            )
            return

        rows = self.all_rows()
        estimated = len(rows) if rows else "tous les"
        answer = QMessageBox.question(
            self,
            "TOUT VÉRIFIER ET CORRIGER",
            "Ce mode va automatiquement :\n\n"
            "• scanner la bibliothèque ;\n"
            "• analyser les vidéos ;\n"
            "• extraire des images ;\n"
            "• vérifier chaque film avec l’IA locale ;\n"
            "• conserver les noms déjà corrects ;\n"
            "• renommer uniquement les erreurs reconnues avec "
            "au moins 95 % de confiance.\n\n"
            "Aucun fichier ne sera supprimé ni déplacé.\n"
            "Chaque renommage pourra être annulé dans l’historique.\n\n"
            f"Lancer le traitement sur {estimated} film(s) ?",
        )
        if answer != QMessageBox.Yes:
            return

        self.run_worker(
            AllInOneWorker(
                folder=folder,
                ffprobe_path=self.ffprobe_edit.text().strip(),
                ffmpeg_path=self.ffmpeg_edit.text().strip(),
                frame_count=max(4, self.frames_spin.value()),
                url=self.ollama_url_edit.text().strip(),
                model=self.ollama_model_edit.text().strip(),
                rename_template=(
                    self.rename_format_edit.text().strip()
                    or "{title} ({year})"
                ),
                skip_unchanged=self.skip_unchanged.isChecked(),
            ),
            "MODE TOUT-EN-UN lancé — ne ferme pas l’application.",
        )

    def start_hybrid(self):
        rows = self.selected_rows()
        if not rows:
            QMessageBox.information(self, "Information", "Aucun film.")
            return

        diagnostics = run_diagnostics({
            **self.config,
            "movies_folder": self.path_edit.text().strip(),
            "ffmpeg_path": self.ffmpeg_edit.text().strip(),
            "ffprobe_path": self.ffprobe_edit.text().strip(),
            "ollama_url": self.ollama_url_edit.text().strip(),
            "ollama_model": self.ollama_model_edit.text().strip(),
        })
        if not diagnostics["ollama"] or not diagnostics["model"]:
            QMessageBox.warning(
                self,
                "IA indisponible",
                diagnostics["ollama_message"]
                + "\n\nInstalle et démarre Ollama avant l’analyse hybride.",
            )
            return

        self.run_worker(
            HybridWorker(
                rows,
                self.ffmpeg_edit.text().strip(),
                min(self.frames_spin.value(), 4),
                self.ollama_url_edit.text().strip(),
                self.ollama_model_edit.text().strip(),
                self.skip_unchanged.isChecked(),
            ),
            f"Analyse hybride lancée sur {len(rows)} film(s)...",
        )

    def start_local_compare(self):
        rows = [row for row in self.selected_rows() if row.get("ai_title")]
        if not rows:
            QMessageBox.information(
                self,
                "Analyse IA requise",
                "Lance d’abord « Vérifier par IA locale » sur les films concernés.",
            )
            return

        self.run_worker(
            LocalCompareWorker(
                rows,
                self.rename_format_edit.text().strip() or "{title} ({year})",
            ),
            f"Préparation locale du renommage pour {len(rows)} film(s)...",
        )

    def start_tmdb(self):
        rows = self.selected_rows()
        if not rows:
            QMessageBox.information(self, "Information", "Aucun film.")
            return

        if not self.tmdb_token_edit.text().strip():
            QMessageBox.warning(
                self,
                "TMDb non configuré",
                "Renseigne ta clé API ou ton jeton TMDb dans les paramètres.",
            )
            return

        self.run_worker(
            TMDbWorker(
                rows,
                self.tmdb_token_edit.text().strip(),
                self.tmdb_language_edit.text().strip() or "fr-FR",
                self.rename_format_edit.text().strip() or "{title} ({year})",
            ),
            f"Comparaison TMDb de {len(rows)} film(s)...",
        )

    def rename_candidates(self):
        rows = self.selected_rows()
        threshold = self.rename_threshold_spin.value() / 100
        return [
            row for row in rows
            if row.get("proposed_filename")
            and float(row.get("comparison_score") or row.get("tmdb_score") or row.get("ai_confidence") or 0) >= threshold
            and row.get("comparison_status") in {
                "confirmed", "rename", "mismatch"
            }
        ]

    def simulate_rename(self):
        rows = self.rename_candidates()
        if not rows:
            QMessageBox.information(
                self,
                "Aucun renommage",
                "Aucun film sélectionné ne dépasse le seuil de confiance.",
            )
            return

        self.run_worker(
            RenameWorker(
                rows,
                True,
                self.rename_threshold_spin.value() / 100,
            ),
            f"Simulation de renommage sur {len(rows)} film(s)...",
        )

    def start_rename(self):
        rows = self.rename_candidates()
        if not rows:
            QMessageBox.information(
                self,
                "Aucun renommage",
                "Aucun film sélectionné ne dépasse le seuil de confiance.",
            )
            return

        preview = "\n".join(
            f"• {row['filename']} → {row['proposed_filename']}"
            for row in rows[:12]
        )
        if len(rows) > 12:
            preview += f"\n… et {len(rows) - 12} autre(s)."

        answer = QMessageBox.warning(
            self,
            "Renommage réel des fichiers",
            f"{len(rows)} fichier(s) vont être renommés sur le NAS.\n\n"
            f"Seuil : {self.rename_threshold_spin.value()} %\n\n"
            f"{preview}\n\n"
            "L’extension sera conservée et les collisions seront bloquées.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.run_worker(
            RenameWorker(
                rows,
                False,
                self.rename_threshold_spin.value() / 100,
            ),
            f"Renommage sécurisé de {len(rows)} film(s)...",
        )

    def undo_rename(self):
        if self.worker_thread is not None:
            QMessageBox.information(
                self,
                "Traitement en cours",
                "Attends la fin du traitement actuel.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Annuler le dernier renommage",
            "Restaurer le dernier nom de fichier modifié ?",
        )
        if answer != QMessageBox.Yes:
            return

        try:
            message = undo_last_rename()
        except Exception as exc:
            QMessageBox.critical(self, "Annulation impossible", str(exc))
            return

        self.log(message)
        self.load_movies()
        QMessageBox.information(self, "Renommage annulé", message)

    def start_audit(self):
        rows = self.all_rows()
        if not rows:
            QMessageBox.information(self, "Information", "Aucun film.")
            return

        self.run_worker(
            AuditWorker(rows),
            f"Audit de {len(rows)} film(s)...",
        )

    def update_progress(self, current, total):
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(current)

    def refresh_dashboard(self):
        stats = dashboard_stats()
        total_size_tb = stats["total_size"] / 1_099_511_627_776

        self.stat_total.value.setText(str(stats["total"]))
        self.stat_size.value.setText(f"{total_size_tb:.2f} To")
        self.stat_analyzed.value.setText(str(stats["analyzed"]))
        self.stat_ai.value.setText(str(stats["ai_checked"]))
        self.stat_duplicates.value.setText(str(stats["duplicates"]))
        self.stat_alerts.value.setText(str(stats["quality_alerts"]))

        self.problem_rename.value.setText(str(stats["rename_ready"]))
        self.problem_mismatch.value.setText(str(stats["mismatches"]))
        self.problem_duplicates.value.setText(str(stats["duplicates"]))
        self.problem_quality.value.setText(str(stats["quality_alerts"]))
        self.problem_errors.value.setText(str(stats["errors"]))

        total = max(1, stats["total"])
        weighted_problems = (
            stats["errors"] * 3
            + stats["mismatches"] * 2
            + stats["quality_alerts"]
        )
        health_exact = max(
            0.0,
            min(100.0, 100.0 - (weighted_problems / total * 100.0)),
        )
        health_display = int(health_exact)
        if weighted_problems == 0:
            health_display = 100
        elif health_display >= 100:
            health_display = 99
        self.health_progress.setValue(health_display)
        self.health_precision.setText(
            f"Santé calculée : {health_exact:.2f} % — "
            f"{stats['errors']} erreur(s), "
            f"{stats['mismatches']} nom(s) incorrect(s)"
        )

        pending_ai = max(0, stats["total"] - stats["ai_checked"])
        if stats["errors"] > 0:
            message = (
                f"{stats['errors']} erreur(s) demandent ton attention."
            )
        elif stats["mismatches"] > 0:
            message = (
                f"{stats['mismatches']} nom(s) semblent incorrects."
            )
        elif stats["rename_ready"] > 0:
            message = (
                f"{stats['rename_ready']} correction(s) sont prêtes à être simulées."
            )
        elif pending_ai > 0:
            message = (
                f"Bibliothèque scannée. {pending_ai} film(s) restent à vérifier par IA."
            )
        else:
            message = "Aucun problème critique détecté."

        self.health_message.setText(message)

    def load_movies(self):
        rows = get_movies(
            self.search.text().strip(),
            self.filter_combo.currentText(),
        )
        self.current_movies = rows

        self.movies.blockSignals(True)
        self.movies.clear()

        for row in rows:
            prefix = ""
            if row["comparison_status"] == "renamed":
                prefix = "✏️ "
            elif row["comparison_status"] == "confirmed":
                prefix = "🟢 "
            elif row["comparison_status"] in ("rename", "mismatch"):
                prefix = "🟠 "
            elif row["ai_status"] == "correct":
                prefix = "✅ "
            elif row["ai_status"] == "mismatch":
                prefix = "❌ "
            elif row["ai_status"] == "uncertain":
                prefix = "⚠ "
            elif row["duplicate_group"]:
                prefix = "♊ "
            elif row["quality_flags"]:
                prefix = "🔎 "
            elif row["frames_ready"]:
                prefix = "🖼 "
            elif row["analyzed"]:
                prefix = "✓ "

            item = QListWidgetItem(prefix + row["filename"])
            item.setData(Qt.UserRole, row["id"])
            self.movies.addItem(item)

        self.movies.blockSignals(False)
        self.refresh_dashboard()
        self.setWindowTitle(
            f"PlexAI Verify v6.0 — {len(rows)} film(s) affiché(s)"
        )

    def show_details(self, current, previous):
        del previous

        if current is None:
            self.details.clear()
            return

        movie_id = current.data(Qt.UserRole)
        movie = next(
            (row for row in self.current_movies if row["id"] == movie_id),
            None,
        )
        if movie is None:
            return

        resolution = "—"
        if movie["width"] and movie["height"]:
            resolution = f"{movie['width']}x{movie['height']}"

        confidence = "—"
        if movie["ai_confidence"] is not None:
            confidence = f"{float(movie['ai_confidence']) * 100:.1f} %"

        bitrate = "—"
        if movie["video_bitrate"]:
            bitrate = f"{float(movie['video_bitrate']) / 1_000_000:.2f} Mb/s"

        duplicate_similarity = "—"
        if movie["duplicate_score"] is not None:
            duplicate_similarity = f"{float(movie['duplicate_score']) * 100:.1f} %"

        text = (
            f"Nom : {movie['filename']}\n\n"
            f"Taille : {(movie['filesize'] or 0) / 1_073_741_824:.2f} Go\n"
            f"Durée : {duration_text(movie['duration'])}\n"
            f"Résolution : {resolution}\n"
            f"Bitrate vidéo : {bitrate}\n"
            f"Codec vidéo : {movie['video_codec'] or '—'}\n"
            f"Codec audio : {movie['audio_codec'] or '—'}\n"
            f"Canaux audio : {movie['audio_channels'] or '—'}\n"
            f"Audio : {movie['audio_languages'] or '—'}\n"
            f"Sous-titres : {movie['subtitle_languages'] or '—'}\n"
            f"HDR : {movie['hdr'] or '—'}\n"
            f"Images extraites : {'Oui' if movie['frames_ready'] else 'Non'}\n\n"
            f"Titre IA : {movie['ai_title'] or '—'}\n"
            f"Année IA : {movie['ai_year'] or '—'}\n"
            f"Confiance : {confidence}\n"
            f"Statut IA : {movie['ai_status'] or '—'}\n"
            f"Notes : {movie['ai_notes'] or '—'}\n\n"
            f"Source comparaison : {movie['comparison_source'] or '—'}\n"
            f"Score comparaison : {float(movie['comparison_score'] or 0) * 100:.1f} %\n"
            f"Titre TMDb : {movie['tmdb_title'] or '—'}\n"
            f"Titre original TMDb : {movie['tmdb_original_title'] or '—'}\n"
            f"Année TMDb : {movie['tmdb_year'] or '—'}\n"
            f"Score TMDb : {float(movie['tmdb_score'] or 0) * 100:.1f} %\n"
            f"Statut comparaison : {movie['comparison_status'] or '—'}\n"
            f"Résultat : {movie['comparison_message'] or '—'}\n"
            f"Nom proposé : {movie['proposed_filename'] or '—'}\n\n"
            f"Groupe doublon : {movie['duplicate_group'] or '—'}\n"
            f"Similarité DNA : {duplicate_similarity}\n"
            f"Score qualité : {movie['quality_score'] if movie['quality_score'] is not None else '—'} / 100\n"
            f"Alertes qualité : {movie['quality_flags'] or '—'}\n"
            f"État analyse : {movie['analysis_state'] or '—'}\n"
            f"Dernière erreur : {movie['last_error'] or '—'}\n"
            f"Code erreur : {movie['error_code'] or '—'}\n"
            f"Action conseillée : {movie['error_action'] or '—'}\n\n"
            f"Chemin :\n{movie['filepath']}"
        )

        self.details.setPlainText(text)

    def export_data(self):
        rows = get_movies(
            self.search.text().strip(),
            self.filter_combo.currentText(),
        )
        if not rows:
            QMessageBox.information(self, "Information", "Aucune donnée.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter",
            "PlexAI-Verify-v1.1.xlsx",
            "Excel (*.xlsx)",
        )
        if not filename:
            return

        try:
            export_excel(rows, filename)
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
            return

        QMessageBox.information(
            self,
            "Export terminé",
            f"Rapport créé :\n{filename}",
        )

    def closeEvent(self, event):
        if (
            self.worker_thread is not None
            and self.worker_thread.isRunning()
        ):
            QMessageBox.warning(
                self,
                "Traitement en cours",
                "Attends la fin du traitement avant de fermer le logiciel.",
            )
            event.ignore()
            return

        event.accept()
