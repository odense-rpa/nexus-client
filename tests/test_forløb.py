import pytest
from unittest.mock import Mock
from httpx import HTTPStatusError

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager


def test_get_citizen_cases(nexus_manager: NexusClientManager, test_borger: dict):
    """Test that citizen has required activePrograms link."""
    # Verify the test citizen has the required link structure
    assert "_links" in test_borger
    assert "activePrograms" in test_borger["_links"]
    assert "href" in test_borger["_links"]["activePrograms"]

    # Test the actual method
    cases = nexus_manager.forløb.hent_forløb(test_borger)

    # Should not raise an exception and should return valid response
    assert cases is None or isinstance(cases, (dict, list))


def test_get_citizen_cases_missing_link(nexus_manager: NexusClientManager):
    """Test handling of citizen without activePrograms link."""
    # Create a mock citizen without the required link
    mock_citizen = {"id": "test-id", "_links": {}}

    # This should raise a KeyError due to missing link
    with pytest.raises(KeyError):
        nexus_manager.forløb.hent_forløb(mock_citizen)


def test_get_citizen_cases_http_error(
    nexus_manager: NexusClientManager, test_borger: dict
):
    """Test handling of HTTP errors."""
    # Mock the client to raise HTTPStatusError
    original_get = nexus_manager.forløb.client.get
    nexus_manager.forløb.client.get = Mock(
        side_effect=HTTPStatusError("Test error", request=Mock(), response=Mock())
    )

    try:
        result = nexus_manager.forløb.hent_forløb(test_borger)
        assert result is None
    finally:
        # Restore original method
        nexus_manager.forløb.client.get = original_get


# Tests for Danish functions
def test_hent_forløb(nexus_manager: NexusClientManager, test_borger: dict):
    """Test hent_forløb function."""
    # Verify the test citizen has the required link structure
    assert "_links" in test_borger
    assert "activePrograms" in test_borger["_links"]
    assert "href" in test_borger["_links"]["activePrograms"]

    # Test the Danish method
    forløb = nexus_manager.forløb.hent_forløb(test_borger)

    # Should not raise an exception and should return valid response
    assert forløb is None or isinstance(forløb, (dict, list))


def test_hent_forløb_missing_link(nexus_manager: NexusClientManager):
    """Test hent_forløb with missing activePrograms link."""
    # Create a mock citizen without the required link
    mock_borger = {"id": "test-id", "_links": {}}

    # This should raise a KeyError due to missing link
    with pytest.raises(KeyError):
        nexus_manager.forløb.hent_forløb(mock_borger)


def test_hent_forløb_http_error(nexus_manager: NexusClientManager, test_borger: dict):
    """Test hent_forløb handling of HTTP errors."""
    # Mock the client to raise HTTPStatusError
    original_get = nexus_manager.forløb.client.get
    nexus_manager.forløb.client.get = Mock(
        side_effect=HTTPStatusError("Test error", request=Mock(), response=Mock())
    )

    try:
        result = nexus_manager.forløb.hent_forløb(test_borger)
        assert result is None
    finally:
        # Restore original method
        nexus_manager.forløb.client.get = original_get


def test_opret_forløb_parameters(nexus_manager: NexusClientManager):
    """Test opret_forløb method exists and has correct parameters."""
    # Test that the method exists
    assert hasattr(nexus_manager.forløb, "opret_forløb")
    assert callable(nexus_manager.forløb.opret_forløb)

    # Test with mock data - this will fail in real test but validates signature
    mock_borger = {
        "_links": {
            "availablePathwayAssociation": {"href": "test-url"},
            "availableProgramPathways": {"href": "test-url"},
        }
    }

    # Mock the HTTP calls to avoid real API calls
    original_get = nexus_manager.forløb.client.get
    mock_response = Mock()
    mock_response.status_code = 404  # Force None return
    mock_response.json.return_value = []
    nexus_manager.forløb.client.get = Mock(return_value=mock_response)

    try:
        # Test that it accepts the correct parameters
        result = nexus_manager.forløb.opret_forløb(mock_borger, "Test grundforløb")
        assert result is None  # Expected due to mocked 404

        result = nexus_manager.forløb.opret_forløb(
            mock_borger, "Test grundforløb", "Test forløb"
        )
        assert result is None  # Expected due to mocked 404
    finally:
        nexus_manager.forløb.client.get = original_get


def test_luk_forløb_parameters(nexus_manager: NexusClientManager):
    """Test luk_forløb method exists and has correct parameters."""
    # Test that the method exists
    assert hasattr(nexus_manager.forløb, "luk_forløb")
    assert callable(nexus_manager.forløb.luk_forløb)

    # Test with mock data
    mock_forløb_ref = {"_links": {"self": {"href": "test-url"}}}

    # Mock the HTTP calls to avoid real API calls
    original_get = nexus_manager.forløb.client.get
    mock_response = Mock()
    mock_response.status_code = 404  # Force False return
    nexus_manager.forløb.client.get = Mock(return_value=mock_response)

    try:
        # Test that it accepts the correct parameters and returns boolean
        result = nexus_manager.forløb.luk_forløb(mock_forløb_ref)
        assert isinstance(result, bool)
        assert result is False  # Expected due to mocked 404
    finally:
        nexus_manager.forløb.client.get = original_get
