from plexai_verify.app.validation_engine import ValidationEngine

def base_movie(**updates):
    movie = {
        "filename": "28 Years Later (2025).mkv", "ai_title": "28 Years Later",
        "ai_year": 2025, "ai_confidence": .98, "tmdb_id": 1,
        "tmdb_title": "28 Years Later", "tmdb_year": 2025, "tmdb_score": .99,
        "analyzed": 1, "duration": 6900, "frames_ready": 1,
        "video_dna": "abc", "proposed_filename": "28 Years Later (2025).mkv",
        "media_kind": "video", "error_code": None,
    }
    movie.update(updates)
    return movie

def test_validated_movie_can_be_corrected():
    result = ValidationEngine().evaluate(base_movie(), True)
    assert result.score >= 95
    assert result.auto_correction_allowed
    assert not result.conflicts

def test_year_conflict_blocks_even_with_high_scores():
    result = ValidationEngine().evaluate(base_movie(ai_year=2000, tmdb_year=2000), True)
    assert result.conflicts
    assert not result.auto_correction_allowed
    assert result.status == "conflict"

def test_missing_visual_and_dna_requires_review():
    result = ValidationEngine().evaluate(base_movie(frames_ready=0, video_dna=None), False)
    assert not result.auto_correction_allowed
