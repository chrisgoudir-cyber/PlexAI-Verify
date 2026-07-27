from __future__ import annotations
from dataclasses import dataclass
from core.repositories.movie_repository import MovieRepository
from core.services.library_service import LibraryService
from core.services.audit_service import AuditService
from core.services.correction_service import CorrectionService

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
