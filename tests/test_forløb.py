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

    assert nexus_manager.forløb.hent_forløb(mock_citizen) is None


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

    assert nexus_manager.forløb.hent_forløb(mock_borger) is None


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


def test_luk_forløb_closes_when_unclosable_link_is_absent(
    nexus_manager: NexusClientManager,
):
    """Test luk_forløb can close payloads without an unclosableReferences link."""
    mock_forløb_ref = {"_links": {"self": {"href": "case-url"}}}

    case_response = Mock()
    case_response.status_code = 200
    case_response.json.return_value = {"_links": {"close": {"href": "close-url"}}}

    close_response = Mock()
    close_response.status_code = 200

    original_get = nexus_manager.forløb.client.get
    original_put = nexus_manager.forløb.client.put
    nexus_manager.forløb.client.get = Mock(return_value=case_response)
    nexus_manager.forløb.client.put = Mock(return_value=close_response)

    try:
        result = nexus_manager.forløb.luk_forløb(mock_forløb_ref)
    finally:
        nexus_manager.forløb.client.get = original_get
        nexus_manager.forløb.client.put = original_put

    assert result is True


def test_luk_forløb_inactivates_when_only_update_link_exists(
    nexus_manager: NexusClientManager,
):
    """Test luk_forløb can inactivate patient pathways with update-only links."""
    from datetime import date

    mock_forløb_ref = {"_links": {"self": {"href": "case-url"}}}
    case_payload = {
        "name": "Udlån",
        "active": True,
        "_links": {"update": {"href": "update-url"}},
    }
    case_response = Mock()
    case_response.status_code = 200
    case_response.json.return_value = case_payload

    update_response = Mock()
    update_response.status_code = 200

    original_get = nexus_manager.forløb.client.get
    original_put = nexus_manager.forløb.client.put
    nexus_manager.forløb.client.get = Mock(return_value=case_response)
    put_mock = Mock(return_value=update_response)
    nexus_manager.forløb.client.put = put_mock

    try:
        result = nexus_manager.forløb.luk_forløb(mock_forløb_ref)
    finally:
        nexus_manager.forløb.client.get = original_get
        nexus_manager.forløb.client.put = original_put

    expected_payload = dict(case_payload)
    expected_payload["active"] = False
    expected_payload["inactivatedDate"] = date.today().isoformat()
    assert result is True
    put_mock.assert_called_once_with("update-url", json=expected_payload)


def test_luk_forløb_inactivates_nested_patient_pathway(
    nexus_manager: NexusClientManager,
):
    """Test luk_forløb follows patientPathway when association has no close link."""
    from datetime import date

    mock_forløb_ref = {"_links": {"self": {"href": "association-url"}}}
    association_response = Mock()
    association_response.status_code = 200
    association_response.json.return_value = {
        "_links": {"patientPathway": {"href": "patient-pathway-url"}}
    }
    patient_pathway_payload = {
        "name": "Udlån",
        "active": True,
        "_links": {"update": {"href": "update-url"}},
    }
    patient_pathway_response = Mock()
    patient_pathway_response.status_code = 200
    patient_pathway_response.json.return_value = patient_pathway_payload
    update_response = Mock()
    update_response.status_code = 200

    original_get = nexus_manager.forløb.client.get
    original_put = nexus_manager.forløb.client.put
    nexus_manager.forløb.client.get = Mock(
        side_effect=[association_response, patient_pathway_response]
    )
    put_mock = Mock(return_value=update_response)
    nexus_manager.forløb.client.put = put_mock

    try:
        result = nexus_manager.forløb.luk_forløb(mock_forløb_ref)
    finally:
        nexus_manager.forløb.client.get = original_get
        nexus_manager.forløb.client.put = original_put

    expected_payload = dict(patient_pathway_payload)
    expected_payload["active"] = False
    expected_payload["inactivatedDate"] = date.today().isoformat()
    assert result is True
    put_mock.assert_called_once_with("update-url", json=expected_payload)


def test_opret_dokument(nexus_manager: NexusClientManager, test_borger: dict):
    pass
    # visning = nexus_manager.borgere.hent_visning(test_borger)
    # assert visning is not None

    # referencer = nexus_manager.borgere.hent_referencer(visning)
    # assert referencer is not None

    # forløb = filter_by_path(
    #        referencer,
    #        "/Sundhedsfagligt grundforløb/Korrespondance - Personlige hjælpemidler",
    #        active_pathways_only=True,
    #    )

    # forløb = nexus_manager.hent_fra_reference(forløb[0])

    # with open("test_file.txt", "rb") as f:
    #    dokument = f.read()

    # oprettet_dokument = nexus_manager.forløb.opret_dokument(
    #    borger=test_borger,
    #    forløb=forløb,
    #    fil=dokument,
    #    filnavn="test_file.txt",
    #    titel="Test Dokument",
    #    noter="Dette er et test dokument",
    #    modtaget=datetime.now(),
    #    indholdstype="text/plain"
    # )


def test_opret_grundforløb_med_forløb(
    nexus_manager: NexusClientManager, test_borger: dict
):
    pass
    # nexus_manager.forløb.opret_forløb(
    #     borger=test_borger,
    #     grundforløb_navn="Test systemadministratorer - grundforløb",
    #     forløb_navn="Test systemadministratorer"
    # )
