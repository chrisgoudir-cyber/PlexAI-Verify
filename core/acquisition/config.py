from __future__ import annotations
import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "radarr": {
        "enabled": False,
        "url": "http://localhost:7878",
        "api_key": "",
        "root_folder": "",
        "quality_profile_id": 1,
        "monitor": "movieOnly",
        "search_on_add": True
    },
    "web_search": {
        "enabled": True,
        "url_template": "https://www.google.com/search?q={query}"
    }
}

def load_config(path: str | Path = "acquisition_config.json") -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        file_path.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return DEFAULT_CONFIG.copy()

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Configuration d'acquisition invalide : {exc}") from exc

    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for section, values in data.items():
        if isinstance(values, dict) and section in merged:
            merged[section].update(values)
        else:
            merged[section] = values
    return merged
