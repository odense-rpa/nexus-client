import pytest

from kmd_nexus_client.utils import sanitize_citizen_identifier, sanitize_cpr


def test_sanitize_citizen_identifier_accepts_anonymous_test_identifier() -> None:
    assert sanitize_citizen_identifier("310299-0018") == "3102990018"


def test_sanitize_cpr_rejects_anonymous_test_identifier_with_invalid_date() -> None:
    with pytest.raises(ValueError, match="Invalid CPR number"):
        sanitize_cpr("310299-0018")


def test_sanitize_cpr_accepts_real_cpr_shape() -> None:
    assert sanitize_cpr("131152-1105") == "1311521105"
