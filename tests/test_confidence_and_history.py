from plexai_verify.core.services.confidence_service import ConfidenceService


def test_confidence_levels():
    assert ConfidenceService.assess(0.96).automatic_allowed is True
    assert ConfidenceService.assess(0.90).level == "review"
    assert ConfidenceService.assess(0.50).level == "ambiguous"


def test_threshold_is_95_percent():
    assert ConfidenceService.AUTO_THRESHOLD == 0.95
