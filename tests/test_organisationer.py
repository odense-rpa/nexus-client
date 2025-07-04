import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.functionality.organisationer import OrganisationerClient
from kmd_nexus_client.functionality.borgere import BorgerClient


def test_hent_organisationer(organisationer_client: OrganisationerClient):
    """Test hent_organisationer Danish function."""
    organisationer = organisationer_client.hent_organisationer()

    assert organisationer is not None
    assert len(organisationer) > 0


def test_hent_leverandører(organisationer_client: OrganisationerClient):
    """Test hent_leverandører Danish function."""
    leverandører = organisationer_client.hent_leverandører()

    assert leverandører is not None
    assert len(leverandører) > 0
    assert all("name" in leverandør for leverandør in leverandører)
    assert all("id" in leverandør for leverandør in leverandører)


def test_opdater_leverandør(organisationer_client: OrganisationerClient, borgere_client: BorgerClient):
    """Test opdater_leverandør Danish function."""
    leverandører = organisationer_client.hent_leverandører()
    leverandør = [x for x in leverandører if x["name"] == "Testleverandør Supporten Træning"][0]
    assert leverandør is not None
    
    opløst_leverandør = borgere_client.client.hent_fra_reference(leverandør)
    opløst_leverandør["address"]["administrativeAreaCode"] = "461"

    opdateret_leverandør = organisationer_client.opdater_leverandør(opløst_leverandør)    
    assert opdateret_leverandør is not None
    assert opdateret_leverandør["address"]["administrativeAreaCode"] == "461"

    # Hent frisk reference i forsøg på at undgå HTTP 409 Conflict
    leverandører = organisationer_client.hent_leverandører()
    leverandør = [x for x in leverandører if x["name"] == "Testleverandør Supporten Træning"][0]
    assert leverandør is not None
    
    opløst_leverandør = borgere_client.client.hent_fra_reference(leverandør)    
    opløst_leverandør["address"]["administrativeAreaCode"] = ""
    
    opdateret_leverandør = organisationer_client.opdater_leverandør(opløst_leverandør)
    assert opdateret_leverandør is not None
    assert opdateret_leverandør["address"]["administrativeAreaCode"] == ""


def test_hent_organisation_ved_navn(organisationer_client: OrganisationerClient):
    """Test hent_organisation_ved_navn Danish function."""
    organisation = organisationer_client.hent_organisation_ved_navn("Sundhedsfagligt Team")

    assert organisation is not None
    assert organisation["name"] == "Sundhedsfagligt Team"


def test_hent_organisationer_for_borger(
    organisationer_client: OrganisationerClient, test_borger: dict
):
    """Test hent_organisationer_for_borger Danish function."""
    organisationer = organisationer_client.hent_organisationer_for_borger(
        test_borger, kun_aktive=False
    )

    assert organisationer is not None
    assert len(organisationer) > 0

    aktive_organisationer = organisationer_client.hent_organisationer_for_borger(
        test_borger, kun_aktive=True
    )

    assert aktive_organisationer is not None
    assert len(aktive_organisationer) > 0
    assert len(aktive_organisationer) <= len(organisationer)
    
    
def test_hent_borgere_for_organisation(organisationer_client: OrganisationerClient):
    """Test hent_borgere_for_organisation Danish function."""
    organisationer = organisationer_client.hent_organisationer()    
    organisation = [x for x in organisationer if x["name"] == "Sundhedsfagligt Team"][0]
    borgere = organisationer_client.hent_borgere_for_organisation(organisation)
    
    assert borgere is not None
    assert len(borgere) > 0


def test_hent_medarbejder_ved_initialer(organisationer_client: OrganisationerClient):
    """Test hent_medarbejder_ved_initialer Danish function."""
    medarbejder = organisationer_client.hent_medarbejder_ved_initialer("roboa")
    
    assert medarbejder is not None
    
    
def test_hent_medarbejdere_for_organisation(organisationer_client: OrganisationerClient):
    """Test hent_medarbejdere_for_organisation Danish function."""
    organisationer = organisationer_client.hent_organisationer()    
    organisation = [x for x in organisationer if x["name"] == "Sundhedsfagligt Team"][0]        
    medarbejdere = organisationer_client.hent_medarbejdere_for_organisation(organisation)
    
    assert medarbejdere is not None
    assert len(medarbejdere) > 0


def test_borger_organisations_relationer(organisationer_client: OrganisationerClient, test_borger: dict):
    """Test Danish functions for citizen-organization relationships."""
    organisation_navn = "Testorganisation Supporten Dag"
    organisationer = organisationer_client.hent_organisationer_for_borger(test_borger)
    filtreret_organisation = next(
        (rel for rel in organisationer if rel["organization"]["name"] == organisation_navn),
        None
    )

    if filtreret_organisation is not None:
        organisationer_client.fjern_borger_fra_organisation(dict(filtreret_organisation))
    
    organisationer = organisationer_client.hent_organisationer_for_borger(test_borger)
    filtreret_organisation = next(
        (rel for rel in organisationer if rel["organization"]["name"] == organisation_navn),
        None
    )

    assert filtreret_organisation is None   
    
    organisation = organisationer_client.hent_organisation_ved_navn(organisation_navn)

    assert organisation is not None
    organisationer_client.tilføj_borger_til_organisation(test_borger, organisation)

    organisationer = organisationer_client.hent_organisationer_for_borger(test_borger)
    filtreret_organisation = next(
        (rel for rel in organisationer if rel["organization"]["name"] == organisation_navn),
        None
    )    
    
    assert filtreret_organisation is not None




# Test error handling
def test_hent_organisation_ved_navn_missing_organization(organisationer_client: OrganisationerClient):
    """Test hent_organisation_ved_navn with non-existent organization."""
    with pytest.raises(IndexError):
        organisationer_client.hent_organisation_ved_navn("NonExistentOrganization")


def test_hent_medarbejder_ved_initialer_missing_professional(organisationer_client: OrganisationerClient):
    """Test hent_medarbejder_ved_initialer with non-existent initials."""
    result = organisationer_client.hent_medarbejder_ved_initialer("xxxxx")
    assert result is None


def test_hent_medarbejder_ved_initialer_api_missing(organisationer_client: OrganisationerClient):
    """Test hent_medarbejder_ved_initialer when API endpoint is missing."""
    # Mock missing API endpoint
    original_api = organisationer_client.nexus_client.api
    organisationer_client.nexus_client.api = {"professionals": None}
    
    try:
        with pytest.raises(ValueError, match="API indeholder ikke professionals endpoint"):
            organisationer_client.hent_medarbejder_ved_initialer("test")
    finally:
        organisationer_client.nexus_client.api = original_api


def test_tilføj_borger_til_organisation_unit_test(organisationer_client: OrganisationerClient):
    """Unit test for tilføj_borger_til_organisation."""
    from unittest.mock import Mock
    
    mock_borger = {
        "_links": {
            "patientOrganizations": {"href": "test-url"}
        }
    }
    mock_organisation = {"id": "123"}
    
    # Mock successful response
    original_put = organisationer_client.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 200
    organisationer_client.nexus_client.put = Mock(return_value=mock_response)
    
    try:
        result = organisationer_client.tilføj_borger_til_organisation(mock_borger, mock_organisation)
        assert result is True
        organisationer_client.nexus_client.put.assert_called_once_with(
            "test-url/123",
            json=""
        )
    finally:
        organisationer_client.nexus_client.put = original_put


def test_fjern_borger_fra_organisation_unit_test(organisationer_client: OrganisationerClient):
    """Unit test for fjern_borger_fra_organisation."""
    from unittest.mock import Mock
    
    mock_relation = {
        "_links": {
            "removeFromPatient": {"href": "test-remove-url"}
        }
    }
    
    # Mock successful response
    original_delete = organisationer_client.nexus_client.delete
    mock_response = Mock()
    mock_response.status_code = 200
    organisationer_client.nexus_client.delete = Mock(return_value=mock_response)
    
    try:
        result = organisationer_client.fjern_borger_fra_organisation(mock_relation)
        assert result is True
        organisationer_client.nexus_client.delete.assert_called_once_with("test-remove-url")
    finally:
        organisationer_client.nexus_client.delete = original_delete


def test_opdater_borger_organisations_relation_unit_test(organisationer_client: OrganisationerClient):
    """Unit test for opdater_borger_organisations_relation."""
    from unittest.mock import Mock
    from datetime import date
    
    mock_relation = {
        "_links": {
            "self": {"href": "test-update-url"}
        }
    }
    
    # Mock successful response
    original_put = organisationer_client.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 200
    organisationer_client.nexus_client.put = Mock(return_value=mock_response)
    
    try:
        result = organisationer_client.opdater_borger_organisations_relation(
            mock_relation, 
            date(2025, 12, 31), 
            True
        )
        assert result is True
        
        # Check that the relation was updated with new values
        expected_relation = dict(mock_relation)
        expected_relation["effectiveEndDate"] = "2025-12-31"
        expected_relation["primaryOrganization"] = True
        
        organisationer_client.nexus_client.put.assert_called_once_with(
            "test-update-url",
            json=expected_relation
        )
    finally:
        organisationer_client.nexus_client.put = original_put


def test_opdater_leverandør_error_handling(organisationer_client: OrganisationerClient):
    """Test opdater_leverandør error handling."""
    from unittest.mock import Mock
    from httpx import HTTPStatusError
    
    mock_leverandør = {
        "_links": {
            "update": {"href": "test-update-url"}
        }
    }
    
    # Mock 404 response
    original_put = organisationer_client.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 404
    error = HTTPStatusError("Not found", request=Mock(), response=mock_response)
    organisationer_client.nexus_client.put = Mock(side_effect=error)
    
    try:
        result = organisationer_client.opdater_leverandør(mock_leverandør)
        assert result is None
    finally:
        organisationer_client.nexus_client.put = original_put


def test_integration_all_danish_methods(organisationer_client: OrganisationerClient, test_borger: dict):
    """Integration test to verify all Danish methods work together."""
    # Test core organization methods
    organisationer = organisationer_client.hent_organisationer()
    assert len(organisationer) > 0
    
    leverandører = organisationer_client.hent_leverandører()
    assert len(leverandører) > 0
    
    # Test organization lookup
    organisation = organisationer_client.hent_organisation_ved_navn("Sundhedsfagligt Team")
    assert organisation is not None
    
    # Test citizen-organization relationships
    borger_organisationer = organisationer_client.hent_organisationer_for_borger(test_borger)
    assert len(borger_organisationer) > 0
    
    # Test organization citizens
    org_borgere = organisationer_client.hent_borgere_for_organisation(organisation)
    assert len(org_borgere) > 0
    
    # Test professional methods
    medarbejder = organisationer_client.hent_medarbejder_ved_initialer("roboa")
    assert medarbejder is not None
    
    org_medarbejdere = organisationer_client.hent_medarbejdere_for_organisation(organisation)
    assert len(org_medarbejdere) > 0
    
    print("✅ Alle danske organisationer metoder fungerer korrekt")