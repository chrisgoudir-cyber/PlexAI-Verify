from __future__ import annotations

from pathlib import Path
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QGridLayout, QTextEdit, QGroupBox, QMessageBox, QFrame,
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)

from plexai_verify.app.paths import DATA_DIR
from plexai_verify.app.dna_repository import get_signature
from plexai_verify.app.database import get_movie, get_connection
from plexai_verify.app.media_support import media_kind
from plexai_verify.app.movie_inspector_model import build_summary
from plexai_verify.app.validation_engine import ValidationEngine
from plexai_verify.core.services.confidence_service import ConfidenceService
from plexai_verify.core.services.correction_service import CorrectionService


def _value(value, suffix=""):
    if value in (None, "", 0):
        return "—"
    return f"{value}{suffix}"


def _bitrate(value):
    if not value:
        return "—"
    return f"{float(value) / 1_000_000:.2f} Mb/s"


def _duration(value):
    if not value:
        return "—"
    seconds = int(float(value))
    return f"{seconds // 3600} h {(seconds % 3600) // 60:02d} min"


def _score_percent(value):
    if value is None:
        return 0
    value = float(value)
    return int(round(value * 100 if value <= 1 else value))


class MovieDialog(QDialog):
    """Film Inspector UX 2027 : fiche visuelle, explicable et sécurisée."""

    CARD = "background:#171c26;border:1px solid #2e3545;border-radius:12px;"
    MUTED = "color:#9299a8;"

    def __init__(self, movie, parent=None):
        super().__init__(parent)
        fresh = get_movie(movie["id"])
        self.movie = dict(fresh) if fresh else dict(movie)
        self.corrections = CorrectionService()
        self.has_dna = bool(get_signature(self.movie["id"]))
        self.validation = ValidationEngine().evaluate(self.movie, self.has_dna)
        self.summary = build_summary(self.movie, self.has_dna)
        title = self.movie.get("tmdb_title") or self.movie.get("ai_title") or self.movie.get("filename") or "Film Inspector"
        self.setWindowTitle(f"{title} — Film Inspector 2.0")
        self.resize(1320, 900)
        self.setMinimumSize(1050, 700)
        self.setStyleSheet("""
            QDialog,QWidget{background:#0f1218;color:#eef1f6;font-family:'Segoe UI';font-size:10pt;}
            QTabWidget::pane{border:0;background:#0f1218;}
            QTabBar::tab{padding:11px 18px;background:#171c26;color:#aeb5c2;border-radius:7px;margin-right:5px;}
            QTabBar::tab:selected{background:#e5a00d;color:#111318;font-weight:800;}
            QGroupBox{font-weight:800;border:1px solid #2e3545;border-radius:10px;margin-top:12px;padding-top:12px;background:#151923;}
            QGroupBox::title{subcontrol-origin:margin;left:12px;padding:0 6px;}
            QPushButton{padding:10px 14px;border-radius:8px;background:#222936;border:1px solid #394153;font-weight:700;}
            QPushButton:hover{background:#2c3444;}
            QPushButton#Primary{background:#e5a00d;color:#111318;border:0;font-weight:900;}
            QPushButton#Danger{background:#48262a;border:1px solid #754047;}
            QProgressBar{height:14px;border:0;border-radius:7px;background:#2a303d;text-align:center;}
            QProgressBar::chunk{border-radius:7px;background:#e5a00d;}
            QTableWidget{background:#151923;border:1px solid #2e3545;gridline-color:#2e3545;}
            QHeaderView::section{background:#202633;padding:8px;border:0;font-weight:800;}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(14)
        root.addWidget(self._build_hero())

        tabs = QTabWidget()
        tabs.addTab(self._build_overview_tab(), "Vue générale")
        tabs.addTab(self._build_metadata_tab(), "Métadonnées")
        tabs.addTab(self._build_technical_tab(), "Technique")
        tabs.addTab(self._build_explanation_tab(), "Pourquoi ce titre ?")
        tabs.addTab(self._build_history_tab(), "Historique")
        root.addWidget(tabs, 1)
        root.addLayout(self._build_actions())
        self._update_action_state()

    def _build_hero(self):
        hero = QFrame(); hero.setStyleSheet(self.CARD)
        row = QHBoxLayout(hero); row.setContentsMargins(18,18,18,18); row.setSpacing(20)
        poster = QLabel(); poster.setFixedSize(170,250); poster.setAlignment(Qt.AlignCenter)
        poster.setStyleSheet("background:#222936;border:1px solid #3a4355;border-radius:10px;color:#9098a8;font-weight:800;")
        poster_path = self.movie.get("tmdb_poster") or ""
        if poster_path and Path(str(poster_path)).exists():
            pixmap=QPixmap(str(poster_path)); poster.setPixmap(pixmap.scaled(170,250,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        elif poster_path:
            poster.setText("AFFICHE TMDB\nÀ METTRE EN CACHE")
            poster.setToolTip(str(poster_path))
        else: poster.setText("AFFICHE\nNON DISPONIBLE")
        row.addWidget(poster)

        center=QVBoxLayout(); center.setSpacing(7)
        title=QLabel(self.movie.get("tmdb_title") or self.movie.get("ai_title") or self.movie.get("filename") or "Film")
        title.setWordWrap(True); title.setStyleSheet("font-size:30px;font-weight:950;color:#fff;")
        center.addWidget(title)
        original=self.movie.get("tmdb_original_title")
        year=self.movie.get("tmdb_year") or self.movie.get("ai_year")
        meta=QLabel("  •  ".join(x for x in [str(year) if year else "Année inconnue", original or "Titre original indisponible"] if x))
        meta.setStyleSheet(self.MUTED+"font-size:14px;"); center.addWidget(meta)

        confidence=float(self.movie.get("comparison_score") or self.movie.get("ai_confidence") or 0)
        assessment=ConfidenceService.assess(confidence)
        validation_label = "VALIDÉ" if self.validation.auto_correction_allowed else "BLOQUÉ" if self.validation.conflicts else "À VÉRIFIER"
        badge=QLabel(f"{validation_label}   SCORE CROISÉ {self.validation.score} %")
        badge.setStyleSheet("padding:9px 12px;background:#252c39;border-radius:8px;font-size:15px;font-weight:900;")
        center.addWidget(badge)
        bar=QProgressBar(); bar.setRange(0,100); bar.setValue(_score_percent(confidence)); bar.setFormat("Confiance globale  %p %")
        center.addWidget(bar)

        current=QLabel(f"Nom actuel   {self.movie.get('filename') or '—'}"); current.setTextInteractionFlags(Qt.TextSelectableByMouse); current.setStyleSheet(self.MUTED)
        proposed=QLabel(f"Nom proposé   {self.movie.get('proposed_filename') or 'Aucune proposition'}"); proposed.setTextInteractionFlags(Qt.TextSelectableByMouse); proposed.setWordWrap(True); proposed.setStyleSheet("font-weight:850;")
        center.addSpacing(4); center.addWidget(current); center.addWidget(proposed); center.addStretch()
        row.addLayout(center,1)

        scorebox=QFrame(); scorebox.setFixedWidth(215); scorebox.setStyleSheet("background:#12161e;border:1px solid #2e3545;border-radius:12px;")
        sl=QVBoxLayout(scorebox); sl.setAlignment(Qt.AlignCenter)
        score=QLabel(str(self.summary.health_score)); score.setAlignment(Qt.AlignCenter); score.setStyleSheet("font-size:48px;font-weight:950;color:#e5a00d;")
        sl.addWidget(QLabel("MOVIE HEALTH SCORE", alignment=Qt.AlignCenter)); sl.addWidget(score); sl.addWidget(QLabel("/ 100", alignment=Qt.AlignCenter))
        edition=QLabel(self.summary.edition_label, alignment=Qt.AlignCenter); edition.setWordWrap(True); edition.setStyleSheet("padding:7px;background:#222936;border-radius:7px;font-weight:800;")
        sl.addWidget(edition)
        row.addWidget(scorebox)
        return hero

    def _build_actions(self):
        row=QHBoxLayout()
        explorer=QPushButton("📁  Ouvrir le dossier"); explorer.clicked.connect(self.open_in_explorer)
        self.ignore_button=QPushButton("⏸  Reporter / Ignorer"); self.ignore_button.clicked.connect(self.ignore_proposal)
        self.apply_button=QPushButton("✓  Corriger maintenant"); self.apply_button.setObjectName("Primary"); self.apply_button.clicked.connect(self.apply_correction)
        close=QPushButton("Fermer"); close.clicked.connect(self.accept)
        row.addWidget(explorer); row.addWidget(self.ignore_button); row.addStretch(); row.addWidget(self.apply_button); row.addWidget(close)
        return row

    def _scroll_tab(self, content):
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(content); return scroll

    def _metric_card(self, title, value, detail=""):
        card=QFrame(); card.setStyleSheet(self.CARD); card.setMinimumHeight(100)
        l=QVBoxLayout(card); v=QLabel(str(value)); v.setStyleSheet("font-size:21px;font-weight:900;"); t=QLabel(title); t.setStyleSheet("font-weight:800;")
        d=QLabel(detail); d.setWordWrap(True); d.setStyleSheet(self.MUTED)
        l.addWidget(v); l.addWidget(t); l.addWidget(d); l.addStretch(); return card

    def _build_overview_tab(self):
        body=QWidget(); layout=QVBoxLayout(body); layout.setSpacing(14)
        grid=QGridLayout(); grid.setSpacing(10)
        code=self.movie.get("error_code"); kind=self.movie.get("media_kind") or media_kind(self.movie.get("filepath", ""))
        status="ISO — montage requis" if code=="ISO_REQUIRES_MOUNT" else (self.movie.get("analysis_state") or "Analysé")
        items=[
            ("Format",kind,"Conteneur média"),("Durée",_duration(self.movie.get("duration")),"Durée FFprobe"),
            ("Taille",f"{(self.movie.get('filesize') or 0)/1_073_741_824:.2f} Go","Poids du fichier"),("État",status,"Diagnostic actuel"),
            ("Vidéo",f"{self.summary.resolution_label} • {_value(self.movie.get('video_codec'))}",_value(self.movie.get('hdr'))),
            ("Audio",self.summary.audio_label,_value(self.movie.get('audio_channels'))),
        ]
        for i,(t,v,d) in enumerate(items): grid.addWidget(self._metric_card(t,v,d),i//3,i%3)
        layout.addLayout(grid)

        if self.movie.get("last_error"):
            diag=QFrame(); diag.setStyleSheet("background:#2a2022;border:1px solid #754047;border-radius:12px;")
            dl=QVBoxLayout(diag); dl.addWidget(QLabel("DIAGNOSTIC", styleSheet="font-size:16px;font-weight:900;")); cause=QLabel(self.movie.get("last_error")); cause.setWordWrap(True); dl.addWidget(cause)
            act=QLabel(self.movie.get("error_action") or "Réessayer l’analyse."); act.setWordWrap(True); act.setStyleSheet(self.MUTED); dl.addWidget(act); layout.addWidget(diag)

        frames=QFrame(); frames.setStyleSheet(self.CARD); fl=QVBoxLayout(frames); fl.addWidget(QLabel("CAPTURES ANALYSÉES", styleSheet="font-size:16px;font-weight:900;"))
        gallery=QHBoxLayout(); frame_dir=Path(DATA_DIR)/"frames"/str(self.movie["id"])
        images=sorted(list(frame_dir.glob("*.jpg"))+list(frame_dir.glob("*.png")))[:4] if frame_dir.exists() else []
        if images:
            for image_path in images:
                lab=QLabel(); lab.setMinimumSize(210,120); lab.setAlignment(Qt.AlignCenter); lab.setStyleSheet("background:#0c0f14;border-radius:8px;")
                lab.setPixmap(QPixmap(str(image_path)).scaled(240,135,Qt.KeepAspectRatio,Qt.SmoothTransformation)); lab.setToolTip(str(image_path)); gallery.addWidget(lab)
        else:
            empty=QLabel("Aucune capture disponible — lance l’analyse visuelle."); empty.setStyleSheet(self.MUTED); gallery.addWidget(empty)
        fl.addLayout(gallery); layout.addWidget(frames)

        notes=QFrame(); notes.setStyleSheet(self.CARD); nl=QVBoxLayout(notes); nl.addWidget(QLabel("SYNTHÈSE IA", styleSheet="font-size:16px;font-weight:900;"))
        text=QTextEdit(); text.setReadOnly(True); text.setMaximumHeight(120); text.setPlainText(self.movie.get("ai_notes") or self.movie.get("comparison_message") or "Aucune justification enregistrée."); nl.addWidget(text); layout.addWidget(notes)
        path=QLabel(f"<b>Chemin du média</b><br>{self.movie.get('filepath') or '—'}"); path.setWordWrap(True); path.setTextInteractionFlags(Qt.TextSelectableByMouse); path.setStyleSheet("padding:12px;background:#151923;border-radius:9px;"); layout.addWidget(path)
        layout.addStretch(); return self._scroll_tab(body)

    def _build_metadata_tab(self):
        body=QWidget(); layout=QVBoxLayout(body); layout.setSpacing(12)
        heading=QLabel("INFORMATIONS DU FILM"); heading.setStyleSheet("font-size:20px;font-weight:950;"); layout.addWidget(heading)
        synopsis=QTextEdit(); synopsis.setReadOnly(True); synopsis.setMinimumHeight(145)
        synopsis.setPlainText(self.movie.get("tmdb_overview") or "Synopsis indisponible. Lance la comparaison TMDB pour enrichir cette fiche.")
        layout.addWidget(synopsis)
        grid=QGridLayout(); grid.setSpacing(10)
        details=[
            ("Titre français", self.movie.get("tmdb_title") or "—"),
            ("Titre original", self.movie.get("tmdb_original_title") or "—"),
            ("Date de sortie", self.movie.get("tmdb_release_date") or self.movie.get("tmdb_year") or "—"),
            ("Réalisateur", self.movie.get("tmdb_director") or "—"),
            ("Genres", self.movie.get("tmdb_genres") or "—"),
            ("Note TMDB", f"{float(self.movie.get('tmdb_vote_average') or 0):.1f} / 10" if self.movie.get("tmdb_vote_average") else "—"),
            ("Identifiant TMDB", self.movie.get("tmdb_id") or "—"),
            ("Identifiant IMDb", self.movie.get("imdb_id") or "—"),
        ]
        for i,(title,value) in enumerate(details): grid.addWidget(self._metric_card(title,value),i//2,i%2)
        layout.addLayout(grid)
        cast=QFrame(); cast.setStyleSheet(self.CARD); cl=QVBoxLayout(cast); cl.addWidget(QLabel("DISTRIBUTION PRINCIPALE", styleSheet="font-size:16px;font-weight:900;"))
        cast_label=QLabel(self.movie.get("tmdb_cast") or "Distribution indisponible."); cast_label.setWordWrap(True); cast_label.setStyleSheet(self.MUTED); cl.addWidget(cast_label); layout.addWidget(cast)
        layout.addStretch(); return self._scroll_tab(body)

    def _build_technical_tab(self):
        body=QWidget(); layout=QVBoxLayout(body); layout.setSpacing(12)
        vg=QGridLayout(); tech=[
            ("📺 Résolution",f"{_value(self.movie.get('width'))} × {_value(self.movie.get('height'))}"),
            ("🎞 Codec vidéo",_value(self.movie.get('video_codec'))),("🌈 HDR",_value(self.movie.get('hdr'))),
            ("📈 Débit vidéo",_bitrate(self.movie.get('video_bitrate'))),("🔊 Codec audio",_value(self.movie.get('audio_codec'))),
            ("🎚 Canaux",_value(self.movie.get('audio_channels'))),("🌍 Langues audio",_value(self.movie.get('audio_languages'))),
            ("💬 Sous-titres",_value(self.movie.get('subtitle_languages'))),
        ]
        for i,(t,v) in enumerate(tech): vg.addWidget(self._metric_card(t,v),i//2,i%2)
        layout.addLayout(vg)
        dna=get_signature(self.movie["id"]); box=QFrame(); box.setStyleSheet(self.CARD); dl=QVBoxLayout(box); dl.addWidget(QLabel("🧬 VIDEO DNA LOCAL", styleSheet="font-size:17px;font-weight:900;"))
        if dna:
            dl.addWidget(QLabel(f"Algorithme : {dna['algorithm']} • {dna['sample_count']} échantillons")); sig=QLabel(dna['signature']); sig.setWordWrap(True); sig.setTextInteractionFlags(Qt.TextSelectableByMouse); sig.setStyleSheet(self.MUTED); dl.addWidget(sig)
        else: dl.addWidget(QLabel("Aucune empreinte locale. Lance « Créer Video DNA »."))
        layout.addWidget(box); layout.addStretch(); return self._scroll_tab(body)

    def _build_explanation_tab(self):
        body=QWidget(); layout=QVBoxLayout(body); layout.setSpacing(10)
        score=float(self.movie.get("comparison_score") or self.movie.get("ai_confidence") or 0); assessment=ConfidenceService.assess(score)
        title=QLabel(f"Pourquoi « {self.movie.get('ai_title') or self.movie.get('tmdb_title') or 'ce titre'} » ?"); title.setStyleSheet("font-size:23px;font-weight:950;"); layout.addWidget(title)
        expl=QLabel(assessment.explanation); expl.setWordWrap(True); expl.setStyleSheet(self.MUTED+"font-size:13px;"); layout.addWidget(expl)
        for label,value,detail in self._evidence_scores(score):
            box=QFrame(); box.setStyleSheet(self.CARD); bl=QVBoxLayout(box); top=QHBoxLayout(); name=QLabel(label); name.setStyleSheet("font-weight:850;"); val=QLabel(f"{value} %"); val.setStyleSheet("font-size:16px;font-weight:900;"); top.addWidget(name); top.addStretch(); top.addWidget(val)
            bar=QProgressBar(); bar.setRange(0,100); bar.setValue(value); bar.setTextVisible(False); d=QLabel(detail); d.setWordWrap(True); d.setStyleSheet(self.MUTED); bl.addLayout(top); bl.addWidget(bar); bl.addWidget(d); layout.addWidget(box)
        conflict_text = "\n".join(f"• {c}" for c in self.validation.conflicts) or "Aucun conflit dur détecté."
        warn=QLabel("Sécurité : aucune correction automatique sous 95 % ou en présence d’un conflit.\n\n" + conflict_text); warn.setWordWrap(True); warn.setStyleSheet("padding:12px;background:#2a2417;border:1px solid #6f5923;border-radius:9px;font-weight:800;"); layout.addWidget(warn); layout.addStretch(); return self._scroll_tab(body)

    def _build_history_tab(self):
        widget=QWidget(); layout=QVBoxLayout(widget)
        with get_connection() as conn:
            rows=conn.execute("SELECT created, old_path, new_path, status, score FROM rename_history WHERE movie_id=? ORDER BY id DESC",(self.movie["id"],)).fetchall()
        table=QTableWidget(len(rows),5); table.setHorizontalHeaderLabels(["Date","Ancien nom","Nouveau nom","État","Confiance"]); table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch); table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        for r,item in enumerate(rows):
            values=[item["created"],Path(item["old_path"]).name,Path(item["new_path"]).name,item["status"],f"{float(item['score'] or 0)*100:.1f} %"]
            for c,value in enumerate(values): table.setItem(r,c,QTableWidgetItem(str(value)))
        layout.addWidget(table)
        if not rows: layout.addWidget(QLabel("Aucune modification enregistrée pour ce film."))
        return widget

    def _edition_label(self):
        text = " ".join(str(self.movie.get(k) or "") for k in ("filename", "ai_notes", "comparison_message")).lower()
        for needle, label in [
            ("director", "Director’s Cut"), ("extended", "Version longue"),
            ("final cut", "Final Cut"), ("remaster", "Remaster"),
            ("imax", "IMAX"),
        ]:
            if needle in text:
                return label
        return "Version non déterminée"

    def _evidence_scores(self, global_score):
        filename = self.movie.get("filename") or ""
        ai_title = self.movie.get("ai_title") or self.movie.get("tmdb_title") or ""
        year_ok = bool(self.movie.get("ai_year") or self.movie.get("tmdb_year"))
        dna_ok = bool(get_signature(self.movie["id"]))
        frames_ok = bool(self.movie.get("frames_ready"))
        tmdb_ok = bool(self.movie.get("tmdb_id"))
        name_score = min(100, max(20, _score_percent(global_score) - (0 if ai_title.lower() in filename.lower() else 8)))
        return [
            ("Nom du fichier", name_score, "Correspondance entre le nom actuel et le titre reconnu."),
            ("Année", 100 if year_ok else 45, "Présence et cohérence de l’année détectée."),
            ("Métadonnées techniques", 95 if self.movie.get("analyzed") else 35, "Durée, résolution, codecs et pistes détectés par FFprobe."),
            ("Images", 98 if frames_ok else 20, "Captures vidéo disponibles pour la reconnaissance visuelle."),
            ("Video DNA", 100 if dna_ok else 0, "Empreinte locale du contenu vidéo."),
            ("TMDB", _score_percent(self.movie.get("tmdb_score")) if tmdb_ok else 0, "Correspondance avec les métadonnées TMDB disponibles."),
        ]

    def _proposal(self):
        return next((p for p in self.corrections.list_proposals() if p.movie_id == int(self.movie["id"])), None)

    def _update_action_state(self):
        proposal = self._proposal()
        self.apply_button.setEnabled(bool(proposal and proposal.safe and self.validation.auto_correction_allowed))
        self.apply_button.setToolTip("" if proposal and proposal.safe else ("Correction bloquée par le moteur de validation." if self.validation.conflicts else proposal.blocking_reason if proposal else "Aucune correction disponible."))
        self.ignore_button.setEnabled(self.movie.get("comparison_status") in ("rename", "mismatch"))

    def apply_correction(self):
        proposal = self._proposal()
        if not proposal or not proposal.safe:
            QMessageBox.warning(self, "Correction", proposal.blocking_reason if proposal else "Aucune correction sûre disponible.")
            return
        answer = QMessageBox.question(self, "Confirmer", f"Renommer :\n{Path(proposal.old_path).name}\n\nen :\n{Path(proposal.new_path).name} ?")
        if answer != QMessageBox.Yes:
            return
        result = self.corrections.apply([self.movie["id"]])[0]
        QMessageBox.information(self, "Correction", result.message)
        self.accept()

    def ignore_proposal(self):
        answer = QMessageBox.question(self, "Ignorer", "Marquer cette proposition comme ignorée ? Le fichier ne sera pas modifié.")
        if answer != QMessageBox.Yes:
            return
        with get_connection() as conn:
            conn.execute(
                """UPDATE movies SET comparison_status='ignored', comparison_message='Proposition ignorée manuellement', updated=CURRENT_TIMESTAMP WHERE id=?""",
                (self.movie["id"],),
            )
        QMessageBox.information(self, "Film Inspector", "Proposition ignorée. Aucun fichier n’a été modifié.")
        self.accept()

    def open_in_explorer(self):
        filepath = self.movie.get("filepath")
        if not filepath:
            return
        try:
            subprocess.Popen(["explorer", "/select,", filepath])
        except Exception as exc:
            QMessageBox.warning(self, "Explorateur Windows", str(exc))
