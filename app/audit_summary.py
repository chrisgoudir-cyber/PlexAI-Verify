from collections import Counter
from app.scoring import global_confidence


def build_audit_summary(movies):
    counts = Counter()
    scores = []

    for movie in movies:
        result = global_confidence(movie)
        scores.append(result["score"])
        counts[result["verdict"]] += 1

        if movie.get("duplicate_group"):
            counts["doublons"] += 1
        if movie.get("last_error"):
            counts["erreurs"] += 1
        if "FRE" not in str(movie.get("audio_languages") or ""):
            counts["sans_audio_fr"] += 1
        if not movie.get("subtitle_languages"):
            counts["sans_sous_titres"] += 1

    return {
        "total": len(movies),
        "conformes": counts["conforme"],
        "probables": counts["probable"],
        "a_verifier": counts["a_verifier"],
        "a_renommer": counts["a_renommer"],
        "doublons": counts["doublons"],
        "erreurs": counts["erreurs"],
        "sans_audio_fr": counts["sans_audio_fr"],
        "sans_sous_titres": counts["sans_sous_titres"],
        "qualite_moyenne": (
            round(sum(scores) / len(scores), 1) if scores else 0
        ),
    }
