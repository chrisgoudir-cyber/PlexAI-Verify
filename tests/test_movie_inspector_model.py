from plexai_verify.app.movie_inspector_model import build_summary, compute_health_score, edition_label, resolution_label


def test_resolution_labels():
    assert resolution_label({"height": 2160}) == "4K UHD"
    assert resolution_label({"height": 1080}) == "1080p"


def test_edition_detection():
    assert edition_label({"filename": "Alien.Directors.Cut.mkv"}) == "Director’s Cut"


def test_health_score_is_bounded():
    movie = {"analyzed": 1, "tmdb_id": 1, "frames_ready": 1, "audio_languages": "fra", "subtitle_languages": "fra", "hdr": "HDR10"}
    assert 0 <= compute_health_score(movie, True) <= 100


def test_summary_prefers_tmdb():
    summary = build_summary({"filename": "x.mkv", "tmdb_title": "Alien", "tmdb_year": 1979, "height": 2160}, False)
    assert summary.display_title == "Alien"
    assert summary.display_year == "1979"
