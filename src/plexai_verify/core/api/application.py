from __future__ import annotations
from dataclasses import dataclass
from plexai_verify.core.repositories.movie_repository import MovieRepository
from plexai_verify.core.services.library_service import LibraryService
from plexai_verify.core.services.audit_service import AuditService
from plexai_verify.core.services.correction_service import CorrectionService

@dataclass
class ApplicationAPI:
    library: LibraryService
    audit: AuditService
    corrections: CorrectionService

    @classmethod
    def create_default(cls) -> 'ApplicationAPI':
        repository=MovieRepository(); repository.initialize()
        return cls(
            library=LibraryService(repository),
            audit=AuditService(repository),
            corrections=CorrectionService(),
        )
