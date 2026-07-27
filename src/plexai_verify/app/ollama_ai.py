import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path


def _image_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def identify_movie(
    frames: list[Path],
    filename: str,
    ollama_url: str,
    model: str,
) -> dict:
    prompt = f"""
Tu analyses des captures issues d'un même long métrage.
Le nom actuel du fichier est : {filename}

Identifie le film uniquement lorsque les images donnent des indices suffisants.
Réponds exclusivement avec un objet JSON valide sous cette forme :
{{
  "title": "titre français ou titre international",
  "year": 2000,
  "confidence": 0.85,
  "status": "correct|mismatch|uncertain",
  "notes": "explication très courte"
}}

Règles :
- confidence doit être entre 0 et 1 ;
- status=correct si le contenu paraît correspondre au nom actuel ;
- status=mismatch si un autre film est clairement reconnu ;
- status=uncertain en cas de doute ;
- n'invente pas de titre.
""".strip()

    payload = {
        "model": model,
        "prompt": prompt,
        "images": [_image_base64(path) for path in frames],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
        },
    }

    request = urllib.request.Request(
        ollama_url.rstrip("/") + "/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Impossible de joindre Ollama. Vérifie qu'Ollama est lancé."
        ) from exc

    raw = str(data.get("response", "")).strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise RuntimeError("Réponse IA non exploitable.")
        result = json.loads(match.group(0))

    return {
        "title": str(result.get("title", "")).strip() or None,
        "year": result.get("year"),
        "confidence": float(result.get("confidence", 0)),
        "status": str(result.get("status", "uncertain")),
        "notes": str(result.get("notes", "")).strip(),
    }



def identify_movie_autopilot(
    frames: list[Path],
    filename: str,
    ollama_url: str,
    model: str,
) -> dict:
    """
    Vérification stricte pour le mode Tout-en-un.

    Le renommage automatique ne sera autorisé que si :
    - le contenu est bien un film ;
    - un titre et une année sont reconnus ;
    - la confiance est >= 0,95 ;
    - le résultat indique clairement que le nom actuel est incorrect.
    """
    prompt = f"""
Tu analyses plusieurs captures extraites du même fichier vidéo.
Nom actuel du fichier : {filename}

Ta mission :
1. déterminer si les captures correspondent bien à un long métrage ;
2. identifier le film uniquement si les indices visuels sont suffisants ;
3. vérifier si le nom actuel correspond au film reconnu.

Réponds exclusivement avec un objet JSON valide :
{{
  "is_movie": true,
  "title": "titre français ou titre international",
  "year": 2000,
  "confidence": 0.97,
  "status": "correct|mismatch|uncertain|not_movie",
  "notes": "raison très courte"
}}

Règles impératives :
- confidence est comprise entre 0 et 1 ;
- status=correct seulement si le contenu correspond au nom actuel ;
- status=mismatch seulement si un autre film est clairement reconnu ;
- status=uncertain dès qu'il existe un doute ;
- status=not_movie si le contenu ne semble pas être un long métrage ;
- n'invente jamais un titre ni une année ;
- une confiance >= 0.95 doit être réservée à une identification très certaine.
""".strip()

    payload = {
        "model": model,
        "prompt": prompt,
        "images": [_image_base64(path) for path in frames],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0},
    }

    request = urllib.request.Request(
        ollama_url.rstrip("/") + "/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Impossible de joindre Ollama. Vérifie qu'Ollama est lancé."
        ) from exc

    raw = str(data.get("response", "")).strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise RuntimeError("Réponse IA non exploitable.")
        result = json.loads(match.group(0))

    is_movie = bool(result.get("is_movie", True))
    status = str(result.get("status", "uncertain")).strip().lower()
    if not is_movie:
        status = "not_movie"

    confidence = max(0.0, min(1.0, float(result.get("confidence", 0) or 0)))
    title = str(result.get("title", "") or "").strip() or None
    year = result.get("year")

    if status not in {"correct", "mismatch", "uncertain", "not_movie"}:
        status = "uncertain"
    if status in {"correct", "mismatch"} and not title:
        status = "uncertain"
    if status == "mismatch" and not year:
        status = "uncertain"

    return {
        "is_movie": is_movie,
        "title": title,
        "year": year,
        "confidence": confidence,
        "status": status,
        "notes": str(result.get("notes", "") or "").strip(),
    }
