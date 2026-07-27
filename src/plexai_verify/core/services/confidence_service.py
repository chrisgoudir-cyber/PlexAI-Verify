from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceAssessment:
    score: float
    level: str
    label: str
    automatic_allowed: bool
    explanation: str


class ConfidenceService:
    """Centralise les seuils de sécurité de PlexAI Verify."""

    AUTO_THRESHOLD = 0.95
    REVIEW_THRESHOLD = 0.80

    @classmethod
    def assess(cls, score: float | None) -> ConfidenceAssessment:
        value = max(0.0, min(1.0, float(score or 0.0)))
        if value >= cls.AUTO_THRESHOLD:
            return ConfidenceAssessment(
                value, "safe", "Renommage sûr", True,
                f"Confiance {value * 100:.1f} % : correction automatique autorisée.",
            )
        if value >= cls.REVIEW_THRESHOLD:
            return ConfidenceAssessment(
                value, "review", "À vérifier", False,
                f"Confiance {value * 100:.1f} % : validation humaine requise.",
            )
        return ConfidenceAssessment(
            value, "ambiguous", "Ambigu", False,
            f"Confiance {value * 100:.1f} % : aucune correction automatique.",
        )
