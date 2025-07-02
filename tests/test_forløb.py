import pytest
from unittest.mock import Mock
from httpx import HTTPStatusError

from .fixtures import cases_client, base_client, test_citizen, citizens_client # noqa: F401
from kmd_nexus_client.functionality.forløb import ForløbClient


def test_get_citizen_cases(cases_client: ForløbClient, test_citizen: dict):
    """Test that citizen has required activePrograms link."""
    # Verify the test citizen has the required link structure
    assert "_links" in test_citizen
    assert "activePrograms" in test_citizen["_links"]
    assert "href" in test_citizen["_links"]["activePrograms"]
    
    # Test the actual method
    cases = cases_client.get_citizen_cases(test_citizen)
    
    # Should not raise an exception and should return valid response
    assert cases is None or isinstance(cases, (dict, list))


def test_get_citizen_cases_missing_link(cases_client: ForløbClient):
    """Test handling of citizen without activePrograms link."""
    # Create a mock citizen without the required link
    mock_citizen = {
        "id": "test-id",
        "_links": {}
    }
    
    # This should raise a KeyError due to missing link
    with pytest.raises(KeyError):
        cases_client.get_citizen_cases(mock_citizen)


def test_get_citizen_cases_http_error(cases_client: ForløbClient, test_citizen: dict):
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
    """Test that ForløbClient initializes correctly."""
    client = ForløbClient(base_client)
    assert client.client == base_client


# Tests for Danish functions
def test_hent_forløb(cases_client: ForløbClient, test_citizen: dict):
    """Test hent_forløb function."""
    # Verify the test citizen has the required link structure
    assert "_links" in test_citizen
    assert "activePrograms" in test_citizen["_links"]
    assert "href" in test_citizen["_links"]["activePrograms"]
    
    # Test the Danish method
    forløb = cases_client.hent_forløb(test_citizen)
    
    # Should not raise an exception and should return valid response
    assert forløb is None or isinstance(forløb, (dict, list))


def test_hent_forløb_missing_link(cases_client: ForløbClient):
    """Test hent_forløb with missing activePrograms link."""
    # Create a mock citizen without the required link
    mock_borger = {
        "id": "test-id",
        "_links": {}
    }
    
    # This should raise a KeyError due to missing link
    with pytest.raises(KeyError):
        cases_client.hent_forløb(mock_borger)


def test_hent_forløb_http_error(cases_client: ForløbClient, test_citizen: dict):
    """Test hent_forløb handling of HTTP errors."""
    # Mock the client to raise HTTPStatusError
    original_get = cases_client.client.get
    cases_client.client.get = Mock(side_effect=HTTPStatusError("Test error", request=Mock(), response=Mock()))
    
    try:
        result = cases_client.hent_forløb(test_citizen)
        assert result is None
    finally:
        # Restore original method
        cases_client.client.get = original_get


def test_opret_forløb_parameters(cases_client: ForløbClient):
    """Test opret_forløb method exists and has correct parameters."""
    # Test that the method exists
    assert hasattr(cases_client, 'opret_forløb')
    assert callable(cases_client.opret_forløb)
    
    # Test with mock data - this will fail in real test but validates signature
    mock_borger = {
        "_links": {
            "availablePathwayAssociation": {"href": "test-url"},
            "availableProgramPathways": {"href": "test-url"}
        }
    }
    
    # Mock the HTTP calls to avoid real API calls
    original_get = cases_client.client.get
    mock_response = Mock()
    mock_response.status_code = 404  # Force None return
    mock_response.json.return_value = []
    cases_client.client.get = Mock(return_value=mock_response)
    
    try:
        # Test that it accepts the correct parameters
        result = cases_client.opret_forløb(mock_borger, "Test grundforløb")
        assert result is None  # Expected due to mocked 404
        
        result = cases_client.opret_forløb(mock_borger, "Test grundforløb", "Test forløb")
        assert result is None  # Expected due to mocked 404
    finally:
        cases_client.client.get = original_get


def test_luk_forløb_parameters(cases_client: ForløbClient):
    """Test luk_forløb method exists and has correct parameters."""
    # Test that the method exists
    assert hasattr(cases_client, 'luk_forløb')
    assert callable(cases_client.luk_forløb)
    
    # Test with mock data
    mock_forløb_ref = {
        "_links": {
            "self": {"href": "test-url"}
        }
    }
    
    # Mock the HTTP calls to avoid real API calls
    original_get = cases_client.client.get
    mock_response = Mock()
    mock_response.status_code = 404  # Force False return
    cases_client.client.get = Mock(return_value=mock_response)
    
    try:
        # Test that it accepts the correct parameters and returns boolean
        result = cases_client.luk_forløb(mock_forløb_ref)
        assert isinstance(result, bool)
        assert result is False  # Expected due to mocked 404
    finally:
        cases_client.client.get = original_get


# Test backward compatibility
def test_backward_compatibility_aliases(cases_client: ForløbClient, test_citizen: dict):
    """Test that old method names still work for backward compatibility."""
    # Test get_citizen_cases alias
    assert hasattr(cases_client, 'get_citizen_cases')
    assert hasattr(cases_client, 'create_citizen_case')
    assert hasattr(cases_client, 'close_case')
    
    # Test that aliases work (using mocked client to avoid real API calls)
    original_get = cases_client.client.get
    mock_response = Mock()
    mock_response.json.return_value = {"test": "data"}
    cases_client.client.get = Mock(return_value=mock_response)
    
    try:
        # Test get_citizen_cases alias
        result1 = cases_client.get_citizen_cases(test_citizen)
        result2 = cases_client.hent_forløb(test_citizen)
        assert result1 == result2
    finally:
        cases_client.client.get = original_get