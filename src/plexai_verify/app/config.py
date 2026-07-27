import json
from plexai_verify.app.paths import CONFIG_PATH

DEFAULT_CONFIG = {
    "movies_folder": r"\\192.168.1.102\Multimedia\Vidéos\Films",
    "ffmpeg_path": r"C:\ffmpeg\bin\ffmpeg.exe",
    "ffprobe_path": r"C:\ffmpeg\bin\ffprobe.exe",
    "ollama_url": "http://127.0.0.1:11434",
    "ollama_model": "qwen2.5vl:7b",
    "frames_per_movie": 8,
    "analysis_profile": "Rapide",
    "skip_unchanged": True,
    "tmdb_token": "",
    "tmdb_language": "fr-FR",
    "rename_format": "{title} ({year})",
    "rename_threshold": 95,
}

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_CONFIG.copy()
    return {**DEFAULT_CONFIG, **data}

def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
