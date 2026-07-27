import os
import sys
from pathlib import Path

APP_NAME = "PlexAI-Verify"


def app_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        path = Path(base) / APP_NAME
    else:
        path = Path.home() / f".{APP_NAME.lower()}"

    path.mkdir(parents=True, exist_ok=True)
    return path


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


DATA_DIR = app_data_dir()
DB_PATH = DATA_DIR / "plexai.db"
CONFIG_PATH = DATA_DIR / "config.json"
CACHE_DIR = DATA_DIR / "cache"
FRAMES_DIR = CACHE_DIR / "frames"
LOGS_DIR = DATA_DIR / "logs"
REPORTS_DIR = DATA_DIR / "reports"

for directory in (CACHE_DIR, FRAMES_DIR, LOGS_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
