import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path


_RELEASE_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\b"
)

_JUNK_PATTERN = re.compile(
    r"\b(?:2160p|1080p|720p|480p|4k|uhd|bluray|blu-ray|bdrip|"
    r"webrip|web-dl|webdl|hdr10|hdr|dv|dolby.?vision|x264|x265|"
    r"h\.?264|h\.?265|hevc|avc|remux|multi|truefrench|french|vostfr|"
    r"proper|repack|extended|director.?s.?cut|aac|dts|atmos)\b",
    re.IGNORECASE,
)


def normalize_text(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def parse_filename(filename):
    stem = Path(filename).stem
    year_match = _RELEASE_PATTERN.search(stem)
    year = int(year_match.group(0)) if year_match else None

    cleaned = stem.replace(".", " ").replace("_", " ")
    cleaned = re.sub(r"\[[^\]]*\]|\([^\)]*\)", " ", cleaned)
    cleaned = _RELEASE_PATTERN.sub(" ", cleaned)
    cleaned = _JUNK_PATTERN.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -._")

    return cleaned or stem, year


def _request_json(url, token):
    headers = {
        "Accept": "application/json",
        "User-Agent": "PlexAI-Verify/0.8",
    }

    if token.startswith("ey"):
        headers["Authorization"] = f"Bearer {token}"

    if not token.startswith("ey"):
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}api_key={urllib.parse.quote(token)}"

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise RuntimeError(
                "Clé ou jeton TMDb refusé."
            ) from exc
        raise RuntimeError(
            f"Erreur TMDb HTTP {exc.code}."
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Impossible de joindre TMDb."
        ) from exc



def _movie_details(movie_id, token, language):
    params = {"language": language or "fr-FR", "append_to_response": "credits,external_ids"}
    url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}?" + urllib.parse.urlencode(params)
    return _request_json(url, token)

def _similarity(a, b):
    return SequenceMatcher(
        None,
        normalize_text(a),
        normalize_text(b),
    ).ratio()


def _candidate_score(candidate, query_title, expected_year):
    title_score = max(
        _similarity(query_title, candidate.get("title")),
        _similarity(query_title, candidate.get("original_title")),
    )

    release_date = candidate.get("release_date") or ""
    try:
        result_year = int(release_date[:4])
    except (TypeError, ValueError):
        result_year = None

    year_score = 0.5
    if expected_year and result_year:
        delta = abs(expected_year - result_year)
        year_score = 1.0 if delta == 0 else 0.7 if delta == 1 else 0.0
    elif not expected_year:
        year_score = 0.75

    popularity = min(float(candidate.get("popularity") or 0) / 100, 1)
    score = title_score * 0.78 + year_score * 0.17 + popularity * 0.05
    return score, result_year


def sanitize_windows_name(name):
    name = re.sub(r'[<>:"/\\|?*]', " - ", str(name))
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:220].strip()


def build_proposed_filename(title, year, extension, template):
    safe_title = sanitize_windows_name(title)
    safe_year = str(year or "").strip()
    try:
        base = template.format(
            title=safe_title,
            year=safe_year,
        )
    except (KeyError, ValueError):
        base = f"{safe_title} ({safe_year})" if safe_year else safe_title

    base = sanitize_windows_name(base)
    if not base:
        raise ValueError("Nom proposé vide.")

    extension = extension if str(extension).startswith(".") else f".{extension}"
    return base + extension.lower()


def compare_movie(movie, token, language, rename_template):
    if not token.strip():
        raise RuntimeError(
            "Renseigne ta clé API ou ton jeton TMDb dans les paramètres."
        )

    filename_title, filename_year = parse_filename(movie["filename"])
    ai_title = str(movie.get("ai_title") or "").strip()
    ai_year = movie.get("ai_year")

    query_title = ai_title or filename_title
    expected_year = ai_year or filename_year

    params = {
        "query": query_title,
        "include_adult": "false",
        "language": language or "fr-FR",
        "page": 1,
    }
    if expected_year:
        params["primary_release_year"] = expected_year

    url = (
        "https://api.themoviedb.org/3/search/movie?"
        + urllib.parse.urlencode(params)
    )
    data = _request_json(url, token.strip())
    candidates = data.get("results") or []

    if not candidates and expected_year:
        params.pop("primary_release_year", None)
        url = (
            "https://api.themoviedb.org/3/search/movie?"
            + urllib.parse.urlencode(params)
        )
        data = _request_json(url, token.strip())
        candidates = data.get("results") or []

    if not candidates:
        return {
            "tmdb_id": None,
            "title": None,
            "original_title": None,
            "year": None,
            "score": 0.0,
            "poster_path": None,
            "comparison_status": "not_found",
            "proposed_filename": None,
        }

    ranked = []
    for candidate in candidates[:12]:
        score, year = _candidate_score(
            candidate,
            query_title,
            expected_year,
        )
        ranked.append((score, year, candidate))

    score, year, best = max(ranked, key=lambda item: item[0])
    title = best.get("title") or best.get("original_title")
    try:
        details = _movie_details(best.get("id"), token.strip(), language)
    except Exception:
        details = best
    credits = details.get("credits") or {}
    crew = credits.get("crew") or []
    cast_items = credits.get("cast") or []
    director = next((item.get("name") for item in crew if item.get("job") == "Director"), None)
    cast = ", ".join(item.get("name") for item in cast_items[:8] if item.get("name"))
    genres = ", ".join(item.get("name") for item in (details.get("genres") or []) if item.get("name"))
    external = details.get("external_ids") or {}
    proposed = build_proposed_filename(
        title,
        year,
        movie.get("extension") or Path(movie["filename"]).suffix,
        rename_template,
    )

    current_stem = normalize_text(Path(movie["filename"]).stem)
    proposed_stem = normalize_text(Path(proposed).stem)
    same_name = current_stem == proposed_stem

    if score >= 0.93 and same_name:
        status = "confirmed"
    elif score >= 0.90:
        status = "rename"
    elif score >= 0.75:
        status = "uncertain"
    else:
        status = "mismatch"

    return {
        "tmdb_id": best.get("id"),
        "title": title,
        "original_title": best.get("original_title"),
        "year": year,
        "score": round(score, 4),
        "poster_path": details.get("poster_path") or best.get("poster_path"),
        "backdrop_path": details.get("backdrop_path") or best.get("backdrop_path"),
        "overview": details.get("overview") or best.get("overview"),
        "director": director,
        "cast": cast,
        "genres": genres,
        "vote_average": details.get("vote_average") or best.get("vote_average"),
        "release_date": details.get("release_date") or best.get("release_date"),
        "imdb_id": external.get("imdb_id"),
        "comparison_status": status,
        "proposed_filename": proposed,
    }
