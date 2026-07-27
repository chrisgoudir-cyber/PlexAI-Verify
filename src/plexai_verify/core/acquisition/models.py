from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class MissingMovie:
    title: str
    year: Optional[int] = None
    collection: str = ""
    external_id: Optional[int] = None
    poster_url: str = ""
    overview: str = ""

    @property
    def display_title(self) -> str:
        return f"{self.title} ({self.year})" if self.year else self.title

@dataclass(slots=True)
class AcquisitionResult:
    success: bool
    message: str
    provider: str
    external_reference: str = ""
