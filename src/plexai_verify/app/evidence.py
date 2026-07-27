from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class EvidenceItem:
    label: str
    value: str
    confidence: float
    source: str = "IA locale"


@dataclass
class VerificationReport:
    title: str
    year: int | None
    confidence: float
    verdict: str
    matches_filename: bool
    evidence: list[EvidenceItem]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "year": self.year,
            "confidence": self.confidence,
            "verdict": self.verdict,
            "matches_filename": self.matches_filename,
            "evidence": [asdict(item) for item in self.evidence],
            "explanation": self.explanation,
        }


def build_report(movie: dict, ai_result: dict) -> VerificationReport:
    evidence = []
    for item in ai_result.get("evidence") or []:
        if isinstance(item, dict):
            evidence.append(EvidenceItem(
                label=str(item.get("label") or "Indice visuel"),
                value=str(item.get("value") or ""),
                confidence=float(item.get("confidence") or 0),
                source=str(item.get("source") or "IA locale"),
            ))

    title = str(ai_result.get("title") or "").strip()
    year = ai_result.get("year")
    confidence = float(ai_result.get("confidence") or 0)
    filename = str(movie.get("filename") or "").lower()

    matches = bool(
        title
        and title.lower() in filename
        and year
        and str(year) in filename
    )

    if matches and confidence >= 0.85:
        verdict = "conforme"
    elif confidence >= 0.85:
        verdict = "contenu_different"
    else:
        verdict = "a_verifier"

    return VerificationReport(
        title=title,
        year=year,
        confidence=confidence,
        verdict=verdict,
        matches_filename=matches,
        evidence=evidence,
        explanation=str(
            ai_result.get("explanation")
            or ai_result.get("notes")
            or ""
        ),
    )
