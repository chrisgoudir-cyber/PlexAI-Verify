import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path


def _exists(command_or_path: str) -> bool:
    value = str(command_or_path or "").strip()
    if not value:
        return False
    path = Path(value)
    return path.exists() or shutil.which(value) is not None


def check_ollama(url: str, model: str) -> dict:
    endpoint = url.rstrip("/") + "/api/tags"
    request = urllib.request.Request(endpoint, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return {
            "ollama": False,
            "model": False,
            "message": "Ollama non joignable",
        }

    names = {
        str(item.get("name") or "")
        for item in data.get("models", [])
    }
    model_ok = model in names or any(
        name.split(":")[0] == model.split(":")[0]
        for name in names
    )
    return {
        "ollama": True,
        "model": model_ok,
        "message": (
            "Ollama et modèle disponibles"
            if model_ok
            else f"Ollama actif, modèle absent : {model}"
        ),
    }


def run_diagnostics(config: dict) -> dict:
    folder = Path(config.get("movies_folder", ""))
    ollama = check_ollama(
        config.get("ollama_url", "http://127.0.0.1:11434"),
        config.get("ollama_model", ""),
    )
    return {
        "library": folder.exists(),
        "ffmpeg": _exists(config.get("ffmpeg_path", "")),
        "ffprobe": _exists(config.get("ffprobe_path", "")),
        "ollama": ollama["ollama"],
        "model": ollama["model"],
        "ollama_message": ollama["message"],
    }
