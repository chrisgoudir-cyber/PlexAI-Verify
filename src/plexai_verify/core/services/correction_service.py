from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from plexai_verify.app.database import get_connection
from plexai_verify.core.services.action_history_service import ActionHistoryService
from plexai_verify.core.services.confidence_service import ConfidenceService


@dataclass(frozen=True)
class CorrectionProposal:
    movie_id: int
    old_path: str
    new_path: str
    score: float
    reason: str
    safe: bool
    blocking_reason: str = ""
    confidence_level: str = "ambiguous"
    confidence_label: str = "Ambigu"


@dataclass(frozen=True)
class CorrectionResult:
    movie_id: int
    status: str
    old_path: str
    new_path: str
    message: str


class CorrectionService:
    MINIMUM_SCORE = ConfidenceService.AUTO_THRESHOLD

    def __init__(self) -> None:
        self.actions = ActionHistoryService()

    def list_proposals(self) -> list[CorrectionProposal]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, filepath, proposed_filename,
                       COALESCE(comparison_score, 0) AS score,
                       COALESCE(comparison_message, '') AS reason
                FROM movies
                WHERE comparison_status IN ('rename', 'mismatch')
                  AND COALESCE(proposed_filename, '') <> ''
                ORDER BY filename COLLATE NOCASE
                """
            ).fetchall()

        proposals: list[CorrectionProposal] = []
        for row in rows:
            old_path = Path(row["filepath"])
            new_path = old_path.with_name(row["proposed_filename"])
            score = float(row["score"] or 0)
            assessment = ConfidenceService.assess(score)

            blocking = ""
            if not assessment.automatic_allowed:
                blocking = assessment.explanation
            elif not old_path.exists():
                blocking = "Le fichier source est introuvable."
            elif new_path.exists() and new_path != old_path:
                blocking = "Un fichier portant déjà ce nom existe."
            elif old_path.suffix.lower() != new_path.suffix.lower():
                blocking = "L’extension du fichier serait modifiée."
            elif old_path.parent != new_path.parent:
                blocking = "Le fichier serait déplacé hors de son dossier."

            proposals.append(CorrectionProposal(
                movie_id=int(row["id"]),
                old_path=str(old_path),
                new_path=str(new_path),
                score=score,
                reason=str(row["reason"] or ""),
                safe=not blocking,
                blocking_reason=blocking,
                confidence_level=assessment.level,
                confidence_label=assessment.label,
            ))
        return proposals

    def apply(self, movie_ids: Iterable[int]) -> list[CorrectionResult]:
        selected = set(int(movie_id) for movie_id in movie_ids)
        proposals = [p for p in self.list_proposals() if p.movie_id in selected]
        action_id = self.actions.start(
            "secure_rename",
            "Renommages sécurisés",
            len(proposals),
            reversible=True,
            metadata={"minimum_confidence": self.MINIMUM_SCORE},
        )
        results: list[CorrectionResult] = []

        for proposal in proposals:
            old_path = Path(proposal.old_path)
            new_path = Path(proposal.new_path)

            if not proposal.safe:
                result = CorrectionResult(proposal.movie_id, "blocked", proposal.old_path, proposal.new_path, proposal.blocking_reason)
                results.append(result)
                self.actions.add_item(action_id, movie_id=proposal.movie_id, item_type="rename", status="blocked", old_value=proposal.old_path, new_value=proposal.new_path, confidence=proposal.score, message=result.message)
                continue

            try:
                old_path.rename(new_path)
                with get_connection() as conn:
                    cur = conn.execute(
                        """
                        INSERT INTO rename_history(movie_id, old_path, new_path, score, status)
                        VALUES (?, ?, ?, ?, 'done')
                        """,
                        (proposal.movie_id, str(old_path), str(new_path), proposal.score),
                    )
                    history_id = int(cur.lastrowid)
                    conn.execute(
                        """
                        UPDATE movies SET filepath=?, filename=?, folder=?, proposed_filename=NULL,
                            comparison_status='confirmed', comparison_message='Nom corrigé et validé',
                            updated=CURRENT_TIMESTAMP WHERE id=?
                        """,
                        (str(new_path), new_path.name, str(new_path.parent), proposal.movie_id),
                    )
                result = CorrectionResult(proposal.movie_id, "done", str(old_path), str(new_path), f"Renommé : {old_path.name} → {new_path.name}")
                results.append(result)
                self.actions.add_item(action_id, movie_id=proposal.movie_id, item_type="rename", status="done", old_value=str(old_path), new_value=str(new_path), confidence=proposal.score, message=result.message, metadata={"rename_history_id": history_id})
            except Exception as exc:
                result = CorrectionResult(proposal.movie_id, "error", str(old_path), str(new_path), str(exc))
                results.append(result)
                self.actions.add_item(action_id, movie_id=proposal.movie_id, item_type="rename", status="error", old_value=str(old_path), new_value=str(new_path), confidence=proposal.score, message=str(exc))

        done = sum(r.status == "done" for r in results)
        blocked = sum(r.status == "blocked" for r in results)
        errors = sum(r.status == "error" for r in results)
        final_status = "completed" if errors == 0 else "completed_with_errors"
        self.actions.finish(action_id, status=final_status, success_count=done, blocked_count=blocked, error_count=errors)
        return results

    def history(self, limit: int = 200):
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT h.*, m.filename AS current_filename
                FROM rename_history h
                LEFT JOIN movies m ON m.id=h.movie_id
                ORDER BY h.id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def undo(self, history_id: int) -> CorrectionResult:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM rename_history WHERE id=?", (history_id,)).fetchone()
        if not row:
            return CorrectionResult(0, "error", "", "", "Historique introuvable.")

        old_path = Path(row["old_path"])
        new_path = Path(row["new_path"])
        action_id = self.actions.start("undo_rename", "Annulation d’un renommage", 1, reversible=False)

        if row["status"] != "done":
            result = CorrectionResult(int(row["movie_id"] or 0), "blocked", str(new_path), str(old_path), "Cette opération a déjà été annulée.")
        elif not new_path.exists():
            result = CorrectionResult(int(row["movie_id"] or 0), "blocked", str(new_path), str(old_path), "Le fichier renommé est introuvable.")
        elif old_path.exists():
            result = CorrectionResult(int(row["movie_id"] or 0), "blocked", str(new_path), str(old_path), "Le nom d’origine est déjà utilisé.")
        else:
            try:
                new_path.rename(old_path)
                with get_connection() as conn:
                    conn.execute("UPDATE rename_history SET status='undone' WHERE id=?", (history_id,))
                    conn.execute(
                        """
                        UPDATE movies SET filepath=?, filename=?, folder=?, comparison_status='rename',
                            proposed_filename=?, comparison_message='Correction annulée', updated=CURRENT_TIMESTAMP
                        WHERE id=?
                        """,
                        (str(old_path), old_path.name, str(old_path.parent), new_path.name, row["movie_id"]),
                    )
                result = CorrectionResult(int(row["movie_id"] or 0), "undone", str(new_path), str(old_path), f"Restauration : {new_path.name} → {old_path.name}")
            except Exception as exc:
                result = CorrectionResult(int(row["movie_id"] or 0), "error", str(new_path), str(old_path), str(exc))

        self.actions.add_item(action_id, movie_id=int(row["movie_id"] or 0), item_type="undo_rename", status=result.status, old_value=result.old_path, new_value=result.new_path, confidence=float(row["score"] or 0), message=result.message, metadata={"rename_history_id": history_id})
        self.actions.finish(action_id, status="completed" if result.status == "undone" else result.status, success_count=int(result.status == "undone"), blocked_count=int(result.status == "blocked"), error_count=int(result.status == "error"))
        return result
