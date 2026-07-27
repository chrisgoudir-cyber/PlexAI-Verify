from __future__ import annotations
from typing import Iterable
from plexai_verify.app import database
from plexai_verify.core.domain.models import LibraryStats, IssueSummary

class MovieRepository:
    """Single gateway between the new core and the legacy SQLite layer."""

    def initialize(self) -> None:
        database.init_database()

    def stats(self) -> LibraryStats:
        return LibraryStats.from_mapping(database.dashboard_stats())

    def list_movies(self, search: str = '', filter_name: str = 'Tous') -> list[dict]:
        return [dict(row) for row in database.get_movies(search, filter_name)]

    def get_movie(self, movie_id: int) -> dict | None:
        row = database.get_movie(movie_id)
        return dict(row) if row else None

    def list_issues(self) -> list[IssueSummary]:
        rows: list[dict] = []
        seen: set[int] = set()
        for filter_name in ('Erreurs','Nom incorrect','À renommer','Doublons','Qualité à contrôler'):
            for row in self.list_movies('', filter_name):
                if row['id'] in seen:
                    continue
                seen.add(row['id']); rows.append(row)
        return [self._to_issue(row) for row in rows]

    @staticmethod
    def _to_issue(movie: dict) -> IssueSummary:
        if movie.get('last_error'):
            issue_type = {
                'ISO_REQUIRES_MOUNT':'ISO à monter',
                'INVALID_MATROSKA':'Fichier MKV invalide',
                'INVALID_MEDIA':'Média illisible',
                'ACCESS_DENIED':'Accès refusé',
                'FILE_MISSING':'Fichier introuvable',
                'TIMEOUT':'Délai dépassé',
            }.get(movie.get('error_code'), 'Erreur d’analyse')
            cause = movie.get('last_error') or 'Erreur inconnue.'
            action = movie.get('error_action') or 'Ouvrir la fiche et relancer l’analyse.'
        elif movie.get('comparison_status') in ('rename','mismatch'):
            issue_type='Nom à corriger'; cause=movie.get('comparison_message') or 'Renommage proposé.'; action='Simuler le renommage puis vérifier la proposition.'
        elif movie.get('duplicate_group'):
            issue_type='Doublon'; cause=f"Groupe {movie.get('duplicate_group')}"; action='Comparer les versions avant toute suppression.'
        else:
            issue_type='Qualité'; cause=movie.get('quality_flags') or 'Contrôle conseillé.'; action='Ouvrir la fiche pour comparer les caractéristiques.'
        return IssueSummary(movie_id=movie['id'], filename=movie.get('filename') or '', issue_type=issue_type, cause=cause, suggested_action=action, ai_title=movie.get('ai_title') or '', proposed_filename=movie.get('proposed_filename') or '', quality_score=movie.get('quality_score'))
