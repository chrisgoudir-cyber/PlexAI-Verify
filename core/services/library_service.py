from __future__ import annotations
from core.domain.models import LibraryStats
from core.repositories.movie_repository import MovieRepository

class LibraryService:
    def __init__(self, repository: MovieRepository):
        self.repository = repository

    def dashboard(self) -> dict:
        stats = self.repository.stats()
        if stats.visible_problem_count == 0:
            headline='Bibliothèque en excellent état'; detail='Aucun problème critique détecté.'
        else:
            headline=f'{stats.visible_problem_count} problème(s) demandent ton attention'
            detail=f'{stats.errors} erreur(s) • {stats.mismatches} nom(s) incorrect(s) • {stats.quality_alerts} alerte(s) qualité'
        display_health = 100 if stats.weighted_problem_count == 0 else min(99, int(stats.health_score))
        return {'stats':stats, 'headline':headline, 'detail':detail, 'health_exact':stats.health_score, 'health_display':display_health}

    def movies(self, search: str='', filter_name: str='Tous') -> list[dict]:
        return self.repository.list_movies(search, filter_name)
