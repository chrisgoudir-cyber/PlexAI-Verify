import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher


def normalize_text(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def sanitize_windows_name(name):
    name = re.sub(r'[<>:"/\\|?*]', " - ", str(name or ""))
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:220].strip()


def build_proposed_filename(title, year, extension, template):
    safe_title = sanitize_windows_name(title)
    safe_year = str(year or "").strip()
    if not safe_title:
        raise ValueError("Titre IA vide.")
    try:
        base = template.format(title=safe_title, year=safe_year)
    except (KeyError, ValueError):
        base = f"{safe_title} ({safe_year})" if safe_year else safe_title
    base = sanitize_windows_name(base)
    if not base:
        raise ValueError("Nom proposé vide.")
    extension = str(extension or "").lower()
    if extension and not extension.startswith("."):
        extension = "." + extension
    return base + extension


def compare_with_local_ai(movie, rename_template):
    title = str(movie.get("ai_title") or "").strip()
    year = movie.get("ai_year")
    confidence = float(movie.get("ai_confidence") or 0)
    status = str(movie.get("ai_status") or "uncertain")

    if not title:
        raise RuntimeError("Aucun titre reconnu par l’IA locale.")

    proposed = build_proposed_filename(
        title,
        year,
        movie.get("extension") or Path(movie["filename"]).suffix,
        rename_template,
    )

    current_stem = normalize_text(Path(movie["filename"]).stem)
    proposed_stem = normalize_text(Path(proposed).stem)
    title_similarity = SequenceMatcher(None, current_stem, proposed_stem).ratio()

    # Le score final reste dominé par la confiance déclarée par l’IA.
    # La similarité du nom ne sert qu’à distinguer un nom déjà conforme d’un renommage.
    score = max(0.0, min(1.0, confidence))

    if score < 0.75 or status == "uncertain":
        comparison_status = "uncertain"
    elif title_similarity >= 0.94:
        comparison_status = "confirmed"
    elif status == "mismatch":
        comparison_status = "mismatch"
    else:
        comparison_status = "rename"

    message = (
        "Nom déjà conforme"
        if comparison_status == "confirmed"
        else "Renommage proposé"
        if comparison_status in ("rename", "mismatch")
        else "Contrôle manuel nécessaire"
    )

    return {
        "comparison_source": "IA locale",
        "comparison_score": round(score, 4),
        "comparison_status": comparison_status,
        "proposed_filename": proposed,
        "comparison_message": message,
    }
