from pathlib import Path

from app.database import insert_movie

VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".m2ts",
    ".ts",
    ".mov",
}


def scan_movies(folder):
    root = Path(folder)

    if not root.exists():
        return []

    movies = []

    for file in root.rglob("*"):

        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:

            insert_movie(
                file.name,
                str(file),
                file.stat().st_size,
            )

            movies.append(file)

    movies.sort()

    return movies