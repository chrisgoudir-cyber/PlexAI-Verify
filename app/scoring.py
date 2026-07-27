def _clamp(value):
    return max(0.0, min(1.0, float(value or 0)))


def global_confidence(movie):
    ai = _clamp(movie.get("ai_confidence"))
    comparison = _clamp(movie.get("comparison_score"))
    dna = _clamp(movie.get("duplicate_score"))
    quality = _clamp((movie.get("quality_score") or 0) / 100)

    name_folder = (
        1.0
        if movie.get("comparison_status") in ("confirmed", "correct")
        else comparison
    )
    metadata = 1.0 if movie.get("analyzed") else 0.0

    components = {
        "nom_dossier_fichier": name_folder,
        "ia_visuelle": ai,
        "metadonnees": metadata,
        "video_dna": dna,
        "qualite_technique": quality,
    }
    weights = {
        "nom_dossier_fichier": 0.25,
        "ia_visuelle": 0.40,
        "metadonnees": 0.15,
        "video_dna": 0.10,
        "qualite_technique": 0.10,
    }
    total = sum(components[k] * weights[k] for k in components)

    if movie.get("last_error"):
        verdict = "erreur"
    elif movie.get("comparison_status") in ("mismatch", "rename"):
        verdict = "a_renommer"
    elif ai and ai < 0.70:
        verdict = "a_verifier"
    elif total >= 0.90:
        verdict = "conforme"
    elif total >= 0.70:
        verdict = "probable"
    else:
        verdict = "a_verifier"

    return {
        "score": round(total * 100, 1),
        "verdict": verdict,
        "components": {
            key: round(value * 100, 1)
            for key, value in components.items()
        },
    }
