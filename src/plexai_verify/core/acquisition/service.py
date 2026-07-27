from __future__ import annotations
from urllib.parse import quote_plus
import webbrowser

from .config import load_config
from .models import MissingMovie, AcquisitionResult
from .radarr import RadarrClient
from .wishlist import WishlistRepository

class AcquisitionService:
    def __init__(self, config_path: str = "acquisition_config.json", db_path: str = "plexai_verify.db") -> None:
        self.config = load_config(config_path)
        self.wishlist = WishlistRepository(db_path)

    def add_to_wishlist(self, movie: MissingMovie) -> AcquisitionResult:
        created = self.wishlist.add(movie)
        message = (
            f"{movie.display_title} ajouté à la Wishlist."
            if created else
            f"{movie.display_title} est déjà dans la Wishlist."
        )
        result = AcquisitionResult(True, message, "Wishlist")
        self.wishlist.log(movie, result.provider, result.success, result.message)
        return result

    def open_web_search(self, movie: MissingMovie) -> AcquisitionResult:
        config = self.config["web_search"]
        if not config.get("enabled", True):
            return AcquisitionResult(False, "Recherche Web désactivée.", "Web")

        template = config.get("url_template", "https://www.google.com/search?q={query}")
        query = quote_plus(f"{movie.title} {movie.year or ''}".strip())
        url = template.replace("{query}", query)
        opened = webbrowser.open(url)
        result = AcquisitionResult(bool(opened), "Recherche ouverte dans le navigateur.", "Web", url)
        self.wishlist.log(movie, result.provider, result.success, result.message)
        return result

    def radarr_client(self) -> RadarrClient:
        config = self.config["radarr"]
        return RadarrClient(
            base_url=config["url"],
            api_key=config["api_key"],
            root_folder=config["root_folder"],
            quality_profile_id=config.get("quality_profile_id", 1),
            monitor=config.get("monitor", "movieOnly"),
            search_on_add=config.get("search_on_add", True),
        )

    def send_to_radarr(self, movie: MissingMovie) -> AcquisitionResult:
        if not self.config["radarr"].get("enabled", False):
            result = AcquisitionResult(False, "Radarr n'est pas activé.", "Radarr")
        else:
            result = self.radarr_client().add_movie(movie)
        self.wishlist.log(movie, result.provider, result.success, result.message)
        return result
