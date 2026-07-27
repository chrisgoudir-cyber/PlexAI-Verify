from __future__ import annotations
import json
from urllib import request, error, parse
from .models import MissingMovie, AcquisitionResult

class RadarrClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        root_folder: str,
        quality_profile_id: int = 1,
        monitor: str = "movieOnly",
        search_on_add: bool = True,
        timeout: int = 15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.root_folder = root_folder
        self.quality_profile_id = int(quality_profile_id)
        self.monitor = monitor
        self.search_on_add = bool(search_on_add)
        self.timeout = timeout

    def _call(self, method: str, path: str, payload: dict | None = None):
        if not self.api_key:
            raise RuntimeError("Clé API Radarr absente.")

        url = f"{self.base_url}/api/v3/{path.lstrip('/')}"
        body = None
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=body, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                return json.loads(content) if content else None
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Radarr HTTP {exc.code} : {details[:300]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Radarr inaccessible : {exc.reason}") from exc

    def ping(self) -> AcquisitionResult:
        try:
            status = self._call("GET", "system/status")
            version = status.get("version", "?") if isinstance(status, dict) else "?"
            return AcquisitionResult(True, f"Radarr connecté — version {version}", "Radarr")
        except Exception as exc:
            return AcquisitionResult(False, str(exc), "Radarr")

    def lookup(self, movie: MissingMovie) -> dict:
        term = parse.quote(movie.display_title)
        results = self._call("GET", f"movie/lookup?term={term}") or []
        if not results:
            raise RuntimeError("Film introuvable dans le catalogue Radarr.")

        if movie.external_id:
            for item in results:
                if item.get("tmdbId") == movie.external_id:
                    return item

        if movie.year:
            for item in results:
                if item.get("title", "").casefold() == movie.title.casefold() and item.get("year") == movie.year:
                    return item

        return results[0]

    def add_movie(self, movie: MissingMovie) -> AcquisitionResult:
        try:
            found = self.lookup(movie)
            payload = {
                "title": found["title"],
                "qualityProfileId": self.quality_profile_id,
                "year": found.get("year"),
                "tmdbId": found.get("tmdbId"),
                "titleSlug": found.get("titleSlug"),
                "images": found.get("images", []),
                "rootFolderPath": self.root_folder,
                "monitored": True,
                "minimumAvailability": "released",
                "monitor": self.monitor,
                "addOptions": {
                    "searchForMovie": self.search_on_add
                },
            }
            result = self._call("POST", "movie", payload)
            reference = str(result.get("id", "")) if isinstance(result, dict) else ""
            return AcquisitionResult(
                True,
                f"{movie.display_title} ajouté à Radarr.",
                "Radarr",
                reference,
            )
        except Exception as exc:
            return AcquisitionResult(False, str(exc), "Radarr")
