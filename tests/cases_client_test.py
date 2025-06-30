import pytest
from unittest.mock import Mock
from httpx import HTTPStatusError

from .fixtures import cases_client, base_client, test_citizen, citizens_client # noqa: F401
from kmd_nexus_client.functionality.cases import CasesClient


def test_get_citizen_cases(cases_client: CasesClient, test_citizen: dict):
    """Test that citizen has required activePrograms link."""
    # Verify the test citizen has the required link structure
    assert "_links" in test_citizen
    assert "activePrograms" in test_citizen["_links"]
    assert "href" in test_citizen["_links"]["activePrograms"]
    
    # Test the actual method
    cases = cases_client.get_citizen_cases(test_citizen)
    
    # Should not raise an exception and should return valid response
    assert cases is None or isinstance(cases, (dict, list))


def test_get_citizen_cases_missing_link(cases_client: CasesClient):
    """Test handling of citizen without activePrograms link."""
    # Create a mock citizen without the required link
    mock_citizen = {
        "id": "test-id",
        "_links": {}
    }
    
    # This should raise a KeyError due to missing link
    with pytest.raises(KeyError):
        cases_client.get_citizen_cases(mock_citizen)


def test_get_citizen_cases_http_error(cases_client: CasesClient, test_citizen: dict):
    """Test handling of HTTP errors."""
    # Mock the client to raise HTTPStatusError
    original_get = cases_client.client.get
    cases_client.client.get = Mock(side_effect=HTTPStatusError("Test error", request=Mock(), response=Mock()))
    
    try:
        result = cases_client.get_citizen_cases(test_citizen)
        assert result is None
    finally:
        # Restore original method
        cases_client.client.get = original_get


def test_cases_client_initialization(base_client):
    """Test that CasesClient initializes correctly."""
    client = CasesClient(base_client)
    assert client.client == base_client