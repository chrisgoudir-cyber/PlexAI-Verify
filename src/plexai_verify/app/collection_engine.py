from __future__ import annotations
import csv, json, re
from dataclasses import dataclass, asdict
from pathlib import Path
from difflib import SequenceMatcher
from plexai_verify.app.database import get_connection

@dataclass(slots=True)
class WishlistItem:
    title: str
    year: int | None
    collection: str
    priority: int = 3
    reason: str = "Film manquant dans la collection"
    status: str = "missing"

def normalize(value: str) -> str:
    value = (value or "").lower()
    value = re.sub(r"\([^)]*\)|\[[^]]*\]", " ", value)
    value = re.sub(r"\b(19|20)\d{2}\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())

class CollectionEngine:
    def __init__(self, catalog_path=None):
        self.catalog_path = Path(catalog_path) if catalog_path else Path(__file__).resolve().parents[1] / "collection_catalog.json"

    def load_catalog(self):
        if not self.catalog_path.exists():
            return []
        data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return data.get("collections", data if isinstance(data, list) else [])

    def library_titles(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT id,filename,ai_title,ai_year,tmdb_title,tmdb_year,tmdb_id,height,hdr,quality_score FROM movies").fetchall()
        result = []
        for row in rows:
            title = row["tmdb_title"] or row["ai_title"] or Path(row["filename"]).stem
            year = row["tmdb_year"] or row["ai_year"]
            item = dict(row)
            item.update(resolved_title=title, resolved_year=year, norm=normalize(title))
            result.append(item)
        return result

    @staticmethod
    def _is_present(item, movies):
        wanted = normalize(item.get("title", ""))
        wanted_year = item.get("year")
        for movie in movies:
            if item.get("tmdb_id") and movie.get("tmdb_id") == item.get("tmdb_id"):
                return True
            ratio = SequenceMatcher(None, wanted, movie["norm"]).ratio()
            year_ok = not wanted_year or not movie.get("resolved_year") or abs(int(wanted_year) - int(movie["resolved_year"])) <= 1
            if ratio >= 0.90 and year_ok:
                return True
        return False

    def analyze(self):
        movies = self.library_titles()
        collections, missing = [], []
        for collection in self.load_catalog():
            items = collection.get("movies", [])
            present = 0
            missing_titles = []
            for item in items:
                if self._is_present(item, movies):
                    present += 1
                else:
                    wish = WishlistItem(item.get("title", "Titre inconnu"), item.get("year"), collection.get("name", "Sans collection"), int(item.get("priority", 3)), item.get("reason", "Film manquant dans la collection"))
                    missing.append(wish)
                    missing_titles.append(wish.title)
            total = len(items)
            collections.append({"name": collection.get("name", "Sans collection"), "present": present, "total": total, "percent": round((present / total) * 100) if total else 0, "missing": missing_titles})
        return collections, missing

    def persist(self, items):
        with get_connection() as conn:
            for item in items:
                conn.execute("""INSERT INTO autonomous_wishlist(title,year,collection_name,priority,reason,status)
                VALUES(?,?,?,?,?,?) ON CONFLICT(title,year,collection_name) DO UPDATE SET priority=excluded.priority,reason=excluded.reason,updated=CURRENT_TIMESTAMP""",
                (item.title,item.year,item.collection,item.priority,item.reason,item.status))

    def export_csv(self, path, items):
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["Titre", "Année", "Collection", "Priorité", "Motif", "Statut"])
            for item in items:
                writer.writerow([item.title, item.year or "", item.collection, item.priority, item.reason, item.status])

    def export_json(self, path, items):
        Path(path).write_text(json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2), encoding="utf-8")
