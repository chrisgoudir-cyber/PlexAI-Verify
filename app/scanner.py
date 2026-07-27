import hashlib
from pathlib import Path

from app.media_support import media_kind

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m2ts", ".ts", ".wmv", ".iso"}

def quick_signature(path: Path, stat) -> str:
    raw = f"{path}|{stat.st_size}|{stat.st_mtime_ns}"
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()

def scan_movies(folder):
    root = Path(folder)
    if not root.exists():
        raise FileNotFoundError(f"Dossier inaccessible : {folder}")
    movies = []
    for file in root.rglob("*"):
        try:
            if not file.is_file() or file.suffix.lower() not in VIDEO_EXTENSIONS:
                continue
            stat = file.stat()
            movies.append({
                "filename": file.name,
                "filepath": str(file),
                "folder": str(file.parent),
                "extension": file.suffix.lower(),
                "filesize": stat.st_size,
                "modified_time": stat.st_mtime,
                "quick_signature": quick_signature(file, stat),
                "media_kind": media_kind(file),
            })
        except OSError:
            continue
    movies.sort(key=lambda x: x["filename"].lower())
    return movies
