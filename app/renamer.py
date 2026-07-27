from pathlib import Path

from app.database import (
    apply_rename,
    last_rename,
    mark_rename_undone,
)


def rename_movie(movie, dry_run=True, minimum_score=0.95):
    score = float(movie.get("comparison_score") or movie.get("tmdb_score") or movie.get("ai_confidence") or 0)
    proposed = str(movie.get("proposed_filename") or "").strip()

    if score < minimum_score:
        raise RuntimeError(
            f"Confiance insuffisante : {score * 100:.1f} %."
        )
    if not proposed:
        raise RuntimeError("Aucun nom proposé.")
    if movie.get("comparison_status") not in {
        "confirmed", "rename", "mismatch"
    }:
        raise RuntimeError("Comparaison TMDb non validée.")

    source = Path(movie["filepath"])
    target = source.with_name(proposed)

    if source.name == target.name:
        return {
            "changed": False,
            "old_path": str(source),
            "new_path": str(target),
            "message": "Le nom est déjà conforme.",
        }

    if target.exists():
        raise FileExistsError(
            f"Le fichier existe déjà : {target.name}"
        )
    if not source.exists():
        raise FileNotFoundError(
            f"Fichier source introuvable : {source}"
        )

    result = {
        "changed": True,
        "old_path": str(source),
        "new_path": str(target),
        "message": (
            f"SIMULATION : {source.name} → {target.name}"
            if dry_run else
            f"RENOMMÉ : {source.name} → {target.name}"
        ),
    }

    if not dry_run:
        source.rename(target)
        apply_rename(
            movie["id"],
            str(source),
            str(target),
            score,
        )

    return result


def undo_last_rename():
    history = last_rename()
    if history is None:
        raise RuntimeError("Aucun renommage à annuler.")

    current = Path(history["new_path"])
    original = Path(history["old_path"])

    if not current.exists():
        raise FileNotFoundError(
            f"Fichier renommé introuvable : {current}"
        )
    if original.exists():
        raise FileExistsError(
            f"Impossible de restaurer : {original.name} existe déjà."
        )

    current.rename(original)
    mark_rename_undone(
        history["id"],
        history["movie_id"],
        str(original),
    )
    return f"Restauré : {current.name} → {original.name}"
