from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class InspectorSummary:
    display_title: str
    display_year: str
    health_score: int
    resolution_label: str
    audio_label: str
    subtitle_label: str
    edition_label: str


def edition_label(movie: dict) -> str:
    explicit = str(movie.get("edition") or "").strip()
    if explicit:
        return explicit
    text = " ".join(str(movie.get(k) or "") for k in ("filename", "ai_notes", "comparison_message")).lower()
    for needle, label in (
        ("director", "Director’s Cut"),
        ("extended", "Version longue"),
        ("final cut", "Final Cut"),
        ("remaster", "Remaster"),
        ("imax", "IMAX"),
    ):
        if needle in text:
            return label
    return "Version non déterminée"


def resolution_label(movie: dict) -> str:
    height = int(movie.get("height") or 0)
    if height >= 2160:
        return "4K UHD"
    if height >= 1440:
        return "1440p"
    if height >= 1080:
        return "1080p"
    if height >= 720:
        return "720p"
    return f"{height}p" if height else "Résolution inconnue"


def compute_health_score(movie: dict, has_dna: bool = False) -> int:
    score = 0
    score += 20 if movie.get("analyzed") else 0
    score += 15 if movie.get("tmdb_id") else 0
    score += 15 if movie.get("frames_ready") else 0
    score += 15 if has_dna else 0
    score += 10 if movie.get("audio_languages") else 0
    score += 8 if movie.get("subtitle_languages") else 0
    score += 7 if movie.get("hdr") else 0
    score += 10 if not movie.get("last_error") else 0
    stored = int(movie.get("quality_score") or 0)
    return max(0, min(100, max(score, stored)))


def build_summary(movie: dict, has_dna: bool = False) -> InspectorSummary:
    title = movie.get("tmdb_title") or movie.get("ai_title") or Path(movie.get("filename") or "Film").stem
    year = movie.get("tmdb_year") or movie.get("ai_year") or "Année inconnue"
    audio = " • ".join(str(x) for x in (movie.get("audio_codec"), movie.get("audio_languages")) if x) or "Audio inconnu"
    subtitles = str(movie.get("subtitle_languages") or "Aucun sous-titre détecté")
    return InspectorSummary(
        display_title=str(title),
        display_year=str(year),
        health_score=compute_health_score(movie, has_dna),
        resolution_label=resolution_label(movie),
        audio_label=audio,
        subtitle_label=subtitles,
        edition_label=edition_label(movie),
    )
