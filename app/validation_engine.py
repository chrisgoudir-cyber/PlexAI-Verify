from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Mapping, Any
from app.tmdb_client import parse_filename, normalize_text

@dataclass(slots=True)
class ValidationResult:
    score: int
    status: str
    auto_correction_allowed: bool
    conflicts: list[str]
    evidence: dict[str, int]
    proposed_filename: str | None

    def to_dict(self) -> dict:
        return asdict(self)

class ValidationEngine:
    """Validation croisée locale. Un conflit dur bloque toujours le renommage."""

    WEIGHTS = {
        "filename": 25,
        "year": 15,
        "technical": 15,
        "tmdb": 20,
        "visual": 15,
        "video_dna": 10,
    }

    @staticmethod
    def _pct(value: Any) -> int:
        if value in (None, ""):
            return 0
        value = float(value)
        return max(0, min(100, round(value * 100 if value <= 1 else value)))

    def evaluate(self, movie: Mapping[str, Any], has_video_dna: bool = False) -> ValidationResult:
        filename = str(movie.get("filename") or "")
        parsed_title, parsed_year = parse_filename(filename)
        tmdb_title = str(movie.get("tmdb_title") or "")
        ai_title = str(movie.get("ai_title") or "")
        proposed_title = tmdb_title or ai_title
        tmdb_year = movie.get("tmdb_year")
        ai_year = movie.get("ai_year")
        proposed_year = tmdb_year or ai_year
        conflicts: list[str] = []

        if parsed_year and proposed_year and int(parsed_year) != int(proposed_year):
            conflicts.append(f"Année contradictoire : fichier {parsed_year}, proposition {proposed_year}.")
        if tmdb_year and ai_year and int(tmdb_year) != int(ai_year):
            conflicts.append(f"Année IA/TMDB contradictoire : IA {ai_year}, TMDB {tmdb_year}.")
        if tmdb_title and ai_title:
            similarity = 100 if normalize_text(tmdb_title) == normalize_text(ai_title) else 0
            if similarity == 0:
                conflicts.append(f"Titre IA/TMDB contradictoire : « {ai_title} » / « {tmdb_title} ».")
        if not movie.get("analyzed") and movie.get("media_kind") not in ("iso", "ISO"):
            conflicts.append("Analyse technique FFprobe absente.")
        if movie.get("error_code") and movie.get("error_code") != "ISO_REQUIRES_MOUNT":
            conflicts.append(f"Erreur d’analyse active : {movie.get('error_code')}.")

        filename_score = self._pct(movie.get("comparison_score") or movie.get("ai_confidence"))
        if proposed_title and normalize_text(proposed_title) in normalize_text(parsed_title):
            filename_score = max(filename_score, 92)
        year_score = 100 if parsed_year and proposed_year and int(parsed_year) == int(proposed_year) else 65 if proposed_year else 20
        technical_score = 100 if movie.get("analyzed") and movie.get("duration") else 35
        tmdb_score = self._pct(movie.get("tmdb_score")) if movie.get("tmdb_id") else 0
        visual_score = 100 if movie.get("frames_ready") else 0
        dna_score = 100 if has_video_dna or movie.get("video_dna") else 0
        evidence = {
            "filename": filename_score,
            "year": year_score,
            "technical": technical_score,
            "tmdb": tmdb_score,
            "visual": visual_score,
            "video_dna": dna_score,
        }
        weighted = sum(evidence[k] * self.WEIGHTS[k] for k in self.WEIGHTS) / 100
        score = round(weighted)
        hard_conflict = bool(conflicts)
        allowed = score >= 95 and not hard_conflict and bool(movie.get("proposed_filename"))
        status = "validated" if allowed else "conflict" if hard_conflict else "manual_review" if score >= 75 else "insufficient"
        return ValidationResult(score, status, allowed, conflicts, evidence, movie.get("proposed_filename"))
