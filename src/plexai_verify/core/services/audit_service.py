from __future__ import annotations
from plexai_verify.core.repositories.movie_repository import MovieRepository

class AuditService:
    def __init__(self, repository: MovieRepository): self.repository=repository
    def issues(self): return self.repository.list_issues()
    def issue_counts(self) -> dict[str,int]:
        counts: dict[str,int]={}
        for issue in self.issues(): counts[issue.issue_type]=counts.get(issue.issue_type,0)+1
        return counts
