import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager


def test_hent_organisationer(nexus_manager: NexusClientManager):
    """Test hent_organisationer Danish function."""
    organisationer = nexus_manager.organisationer.hent_organisationer()

    assert organisationer is not None
    assert len(organisationer) > 0

def test_hent_organisationer_med_træhierarki(nexus_manager: NexusClientManager):
    """Test hent_organisationer_med_træhierarki Danish function."""
    organisationer_tree = nexus_manager.organisationer.hent_organisationer_med_træhierarki()

    assert organisationer_tree is not None
    assert isinstance(organisationer_tree, dict), "Tree should be a dictionary"
    assert "name" in organisationer_tree, "Root organization should have a name"
    assert "children" in organisationer_tree, "Root organization should have children"
    assert len(organisationer_tree.get("children", [])) > 0, "Root should have child organizations"

def test_hent_organisationer_med_træhierarki_med_godkendt_liste(nexus_manager: NexusClientManager):
    """Test hent_organisationer_med_træhierarki Danish function with approved list."""
    from kmd_nexus_client.tree_helpers import find_nodes
    
    godkendt_liste = ["Lysningen",
                    "Erhvervet hjerneskade",
                    "Fysisk Funktionsnedsættelse",
                    "E-Team",
                    "Vedvarende sygdomsudvikling 1",
                    "Vedvarende sygdomsudvikling 2",
                    "Kære Pleje Odense ApS",
                    "Svane Pleje, Syd ApS"
    ]
    organisationer_tree = nexus_manager.organisationer.hent_organisationer_med_træhierarki()

    # Find all organizations in the tree that match the approved list
    filtrerede_organisationer = find_nodes(
        organisationer_tree, 
        lambda org: org.get("name", "") in godkendt_liste
    )

    assert organisationer_tree is not None
    assert len(filtrerede_organisationer) == len(godkendt_liste), f"Expected {len(godkendt_liste)} organizations, but found {len(filtrerede_organisationer)}"
    assert all(
        org["name"] in godkendt_liste for org in filtrerede_organisationer
    ), "Alle organisationer i den filtrerede liste skal være i den godkendte liste"


def test_hent_leverandører(nexus_manager: NexusClientManager):
    """Test hent_leverandører Danish function."""
    leverandører = nexus_manager.organisationer.hent_leverandører()

    assert leverandører is not None
    assert len(leverandører) > 0
    assert all("name" in leverandør for leverandør in leverandører)
    assert all("id" in leverandør for leverandør in leverandører)


def test_opdater_leverandør(nexus_manager: NexusClientManager):
    """Test opdater_leverandør Danish function."""
    leverandører = nexus_manager.organisationer.hent_leverandører()
    leverandør = [
        x for x in leverandører if x["name"] == "Testleverandør Supporten Træning"
    ][0]
    assert leverandør is not None

    opløst_leverandør = nexus_manager.hent_fra_reference(leverandør)
    opløst_leverandør["address"]["administrativeAreaCode"] = "461"

    opdateret_leverandør = nexus_manager.organisationer.opdater_leverandør(
        opløst_leverandør
    )
    assert opdateret_leverandør is not None
    assert opdateret_leverandør["address"]["administrativeAreaCode"] == "461"

    # Hent frisk reference i forsøg på at undgå HTTP 409 Conflict
    leverandører = nexus_manager.organisationer.hent_leverandører()
    leverandør = [
        x for x in leverandører if x["name"] == "Testleverandør Supporten Træning"
    ][0]
    assert leverandør is not None

    opløst_leverandør = nexus_manager.hent_fra_reference(leverandør)
    opløst_leverandør["address"]["administrativeAreaCode"] = ""

    opdateret_leverandør = nexus_manager.organisationer.opdater_leverandør(
        opløst_leverandør
    )
    assert opdateret_leverandør is not None
    assert opdateret_leverandør["address"]["administrativeAreaCode"] == ""


def test_hent_organisation_ved_navn(nexus_manager: NexusClientManager):
    """Test hent_organisation_ved_navn Danish function."""
    organisation = nexus_manager.organisationer.hent_organisation_ved_navn(
        "Sundhedsfagligt Team"
    )

    assert organisation is not None
    assert organisation["name"] == "Sundhedsfagligt Team"

    # Test med en ikke eksisterende organisation
    organisation = nexus_manager.organisationer.hent_organisation_ved_navn(
        "Ikke-eksisterende Organisation"
    )

    assert organisation is None


def test_hent_organisationer_for_borger(
    nexus_manager: NexusClientManager, test_borger: dict
):
    """Test hent_organisationer_for_borger Danish function."""
    organisationer = nexus_manager.organisationer.hent_organisationer_for_borger(
        test_borger, kun_aktive=False
    )

    assert organisationer is not None
    assert len(organisationer) > 0

    aktive_organisationer = nexus_manager.organisationer.hent_organisationer_for_borger(
        test_borger, kun_aktive=True
    )

    assert aktive_organisationer is not None
    assert len(aktive_organisationer) > 0
    assert len(aktive_organisationer) <= len(organisationer)


def test_hent_borgere_for_organisation(nexus_manager: NexusClientManager):
    """Test hent_borgere_for_organisation Danish function."""
    organisationer = nexus_manager.organisationer.hent_organisationer()
    organisation = [x for x in organisationer if x["name"] == "Sundhedsfagligt Team"][0]
    borgere = nexus_manager.organisationer.hent_borgere_for_organisation(organisation)

    assert borgere is not None
    assert len(borgere) > 0


def test_hent_medarbejder_ved_initialer(nexus_manager: NexusClientManager):
    """Test hent_medarbejder_ved_initialer Danish function."""
    medarbejder = nexus_manager.organisationer.hent_medarbejder_ved_initialer("roboa")

    assert medarbejder is not None


def test_hent_medarbejdere_for_organisation(nexus_manager: NexusClientManager):
    """Test hent_medarbejdere_for_organisation Danish function."""
    organisationer = nexus_manager.organisationer.hent_organisationer()
    organisation = [x for x in organisationer if x["name"] == "Sundhedsfagligt Team"][0]
    medarbejdere = nexus_manager.organisationer.hent_medarbejdere_for_organisation(
        organisation
    )

    assert medarbejdere is not None
    assert len(medarbejdere) > 0


def test_borger_organisations_relationer(
    nexus_manager: NexusClientManager, test_borger: dict
):
    """Test Danish functions for citizen-organization relationships."""
    organisation_navn = "Testorganisation Supporten Dag"
    organisationer = nexus_manager.organisationer.hent_organisationer_for_borger(
        test_borger
    )
    filtreret_organisation = next(
        (
            rel
            for rel in organisationer
            if rel["organization"]["name"] == organisation_navn
        ),
        None,
    )

    if filtreret_organisation is not None:
        nexus_manager.organisationer.fjern_borger_fra_organisation(
            dict(filtreret_organisation)
        )

    organisationer = nexus_manager.organisationer.hent_organisationer_for_borger(
        test_borger
    )
    filtreret_organisation = next(
        (
            rel
            for rel in organisationer
            if rel["organization"]["name"] == organisation_navn
        ),
        None,
    )

    assert filtreret_organisation is None

    organisation = nexus_manager.organisationer.hent_organisation_ved_navn(
        organisation_navn
    )

    assert organisation is not None
    nexus_manager.organisationer.tilføj_borger_til_organisation(
        test_borger, organisation
    )

    organisationer = nexus_manager.organisationer.hent_organisationer_for_borger(
        test_borger
    )
    filtreret_organisation = next(
        (
            rel
            for rel in organisationer
            if rel["organization"]["name"] == organisation_navn
        ),
        None,
    )

    assert filtreret_organisation is not None


# Test error handling
def test_hent_organisation_ved_navn_missing_organization(
    nexus_manager: NexusClientManager,
):
    """Test hent_organisation_ved_navn with non-existent organization."""
    with pytest.raises(IndexError):
        nexus_manager.organisationer.hent_organisation_ved_navn(
            "NonExistentOrganization"
        )


def test_hent_medarbejder_ved_initialer_missing_professional(
    nexus_manager: NexusClientManager,
):
    """Test hent_medarbejder_ved_initialer with non-existent initials."""
    result = nexus_manager.organisationer.hent_medarbejder_ved_initialer("xxxxx")
    assert result is None


def test_hent_medarbejder_ved_initialer_api_missing(nexus_manager: NexusClientManager):
    """Test hent_medarbejder_ved_initialer when API endpoint is missing."""
    # Mock missing API endpoint
    original_api = nexus_manager.organisationer.nexus_client.api
    nexus_manager.organisationer.nexus_client.api = {"professionals": None}

    try:
        with pytest.raises(
            ValueError, match="API indeholder ikke professionals endpoint"
        ):
            nexus_manager.organisationer.hent_medarbejder_ved_initialer("test")
    finally:
        nexus_manager.organisationer.nexus_client.api = original_api


def test_tilføj_borger_til_organisation_unit_test(nexus_manager: NexusClientManager):
    """Unit test for tilføj_borger_til_organisation."""
    from unittest.mock import Mock

    mock_borger = {"_links": {"patientOrganizations": {"href": "test-url"}}}
    mock_organisation = {"id": "123"}

    # Mock successful response
    original_put = nexus_manager.organisationer.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 200
    nexus_manager.organisationer.nexus_client.put = Mock(return_value=mock_response)

    try:
        result = nexus_manager.organisationer.tilføj_borger_til_organisation(
            mock_borger, mock_organisation
        )
        assert result is True
        nexus_manager.organisationer.nexus_client.put.assert_called_once_with(
            "test-url/123", json=""
        )
    finally:
        nexus_manager.organisationer.nexus_client.put = original_put


def test_fjern_borger_fra_organisation_unit_test(nexus_manager: NexusClientManager):
    """Unit test for fjern_borger_fra_organisation."""
    from unittest.mock import Mock

    mock_relation = {"_links": {"removeFromPatient": {"href": "test-remove-url"}}}

    # Mock successful response
    original_delete = nexus_manager.organisationer.nexus_client.delete
    mock_response = Mock()
    mock_response.status_code = 200
    nexus_manager.organisationer.nexus_client.delete = Mock(return_value=mock_response)

    try:
        result = nexus_manager.organisationer.fjern_borger_fra_organisation(
            mock_relation
        )
        assert result is True
        nexus_manager.organisationer.nexus_client.delete.assert_called_once_with(
            "test-remove-url"
        )
    finally:
        nexus_manager.organisationer.nexus_client.delete = original_delete


def test_opdater_borger_organisations_relation_unit_test(
    nexus_manager: NexusClientManager,
):
    """Unit test for opdater_borger_organisations_relation."""
    from unittest.mock import Mock
    from datetime import date

    mock_relation = {"_links": {"self": {"href": "test-update-url"}}}

    # Mock successful response
    original_put = nexus_manager.organisationer.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 200
    nexus_manager.organisationer.nexus_client.put = Mock(return_value=mock_response)

    try:
        result = nexus_manager.organisationer.opdater_borger_organisations_relation(
            mock_relation, date(2025, 12, 31), True
        )
        assert result is True

        # Check that the relation was updated with new values
        expected_relation = dict(mock_relation)
        expected_relation["effectiveEndDate"] = "2025-12-31"
        expected_relation["primaryOrganization"] = True

        nexus_manager.organisationer.nexus_client.put.assert_called_once_with(
            "test-update-url", json=expected_relation
        )
    finally:
        nexus_manager.organisationer.nexus_client.put = original_put


def test_opdater_leverandør_error_handling(nexus_manager: NexusClientManager):
    """Test opdater_leverandør error handling."""
    from unittest.mock import Mock
    from httpx import HTTPStatusError

    mock_leverandør = {"_links": {"update": {"href": "test-update-url"}}}

    # Mock 404 response
    original_put = nexus_manager.organisationer.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 404
    error = HTTPStatusError("Not found", request=Mock(), response=mock_response)
    nexus_manager.organisationer.nexus_client.put = Mock(side_effect=error)

    try:
        result = nexus_manager.organisationer.opdater_leverandør(mock_leverandør)
        assert result is None
    finally:
        nexus_manager.organisationer.nexus_client.put = original_put


def test_integration_all_danish_methods(
    nexus_manager: NexusClientManager, test_borger: dict
):
    """Integration test to verify all Danish methods work together."""
    # Test core organization methods
    organisationer = nexus_manager.organisationer.hent_organisationer()
    assert len(organisationer) > 0

    leverandører = nexus_manager.organisationer.hent_leverandører()
    assert len(leverandører) > 0

    # Test organization lookup
    organisation = nexus_manager.organisationer.hent_organisation_ved_navn(
        "Sundhedsfagligt Team"
    )
    assert organisation is not None

    # Test citizen-organization relationships
    borger_organisationer = nexus_manager.organisationer.hent_organisationer_for_borger(
        test_borger
    )
    assert len(borger_organisationer) > 0

    # Test organization citizens
    org_borgere = nexus_manager.organisationer.hent_borgere_for_organisation(
        organisation
    )
    assert len(org_borgere) > 0

    # Test professional methods
    medarbejder = nexus_manager.organisationer.hent_medarbejder_ved_initialer("roboa")
    assert medarbejder is not None

    org_medarbejdere = nexus_manager.organisationer.hent_medarbejdere_for_organisation(
        organisation
    )
    assert len(org_medarbejdere) > 0

    print("✅ Alle danske organisationer metoder fungerer korrekt")
