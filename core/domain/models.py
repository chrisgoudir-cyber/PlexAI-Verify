from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class LibraryStats:
    total: int = 0
    total_size: int = 0
    analyzed: int = 0
    ai_checked: int = 0
    duplicates: int = 0
    quality_alerts: int = 0
    errors: int = 0
    mismatches: int = 0
    rename_ready: int = 0

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> 'LibraryStats':
        values = {name: int(row.get(name, 0) or 0) for name in cls.__dataclass_fields__}
        return cls(**values)

    @property
    def weighted_problem_count(self) -> int:
        return self.errors * 3 + self.mismatches * 2 + self.quality_alerts

    @property
    def health_score(self) -> float:
        if self.total <= 0:
            return 100.0
        return max(0.0, min(100.0, 100.0 - self.weighted_problem_count / self.total * 100.0))

    @property
    def visible_problem_count(self) -> int:
        return self.errors + self.mismatches + self.quality_alerts

@dataclass(frozen=True)
class IssueSummary:
    movie_id: int
    filename: str
    issue_type: str
    cause: str
    suggested_action: str
    ai_title: str = ''
    proposed_filename: str = ''
    quality_score: int | None = None
