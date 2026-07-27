import re
import unicodedata
from pathlib import Path

GENERIC_NAMES = re.compile(
    r"^(film|movie|video|vidéo|titre|unknown|inconnu|sample|temp|"
    r"fichier|nouveau|copy|copie)[\s._-]*\d*$",
    re.IGNORECASE,
)
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
RELEASE_TAGS = re.compile(
    r"\b(?:2160p|1080p|720p|4k|uhd|bluray|web.?dl|webrip|"
    r"bdrip|x264|x265|hevc|hdr|dv|multi|french|vostfr|remux)\b",
    re.IGNORECASE,
)


def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def express_decision(movie: dict) -> dict:
    path = Path(movie["filepath"])
    stem = path.stem
    folder_name = path.parent.name

    readable = re.sub(r"[._]+", " ", stem).strip()
    normalized_file = normalize(stem)
    normalized_folder = normalize(folder_name)

    has_year = bool(YEAR.search(readable))
    generic = bool(GENERIC_NAMES.fullmatch(readable))
    release_tags = len(RELEASE_TAGS.findall(readable))
    has_metadata = bool(movie.get("analyzed"))

    # Cas idéal Plex : dossier et fichier portent exactement le même titre.
    if normalized_folder and normalized_folder == normalized_file and has_year:
        return {
            "needs_ai": False,
            "status": "confirmed",
            "reason": "dossier et fichier identiques avec année",
        }

    if generic or len(readable) < 4:
        return {
            "needs_ai": True,
            "status": "needs_ai",
            "reason": "nom générique ou inexploitable",
        }

    if movie.get("ai_status"):
        return {
            "needs_ai": False,
            "status": "already_checked",
            "reason": "déjà vérifié par l’IA",
        }

    if has_year and release_tags == 0 and has_metadata:
        return {
            "needs_ai": False,
            "status": "confirmed",
            "reason": "nom déjà normalisé avec année",
        }

    if has_year and release_tags <= 2 and has_metadata:
        return {
            "needs_ai": False,
            "status": "likely_ok",
            "reason": "nom exploitable ; contrôle IA non prioritaire",
        }

    return {
        "needs_ai": True,
        "status": "needs_ai",
        "reason": "nom bruité ou ambigu",
    }
