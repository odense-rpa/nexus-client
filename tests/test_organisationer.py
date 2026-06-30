import os
from typing import Any

import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.functionality.organisationer import (
    OrganisationerClient,
    hcl_depot_orders_endpoint,
)
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.tree_helpers import filter_by_path


def test_hent_organisationer(nexus_manager: NexusClientManager):
    """Test hent_organisationer Danish function."""
    organisationer = nexus_manager.organisationer.hent_organisationer()

    assert organisationer is not None
    assert len(organisationer) > 0


def test_hent_organisationer_med_træhierarki(nexus_manager: NexusClientManager):
    """Test hent_organisationer_med_træhierarki Danish function."""
    organisationer_tree = (
        nexus_manager.organisationer.hent_organisationer_med_træhierarki()
    )

    assert organisationer_tree is not None
    assert isinstance(organisationer_tree, dict), "Tree should be a dictionary"
    assert "name" in organisationer_tree, "Root organization should have a name"
    assert "children" in organisationer_tree, "Root organization should have children"
    assert len(organisationer_tree.get("children", [])) > 0, (
        "Root should have child organizations"
    )


def test_hent_leverandører(nexus_manager: NexusClientManager):
    """Test hent_leverandører Danish function."""
    leverandører = nexus_manager.organisationer.hent_leverandører()

    assert leverandører is not None
    assert len(leverandører) > 0
    assert all("name" in leverandør for leverandør in leverandører)
    assert all("id" in leverandør for leverandør in leverandører)


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


def test_fjern_borger_fra_organisation_returns_false_when_remove_link_is_missing(
    nexus_manager: NexusClientManager,
):
    """Unit test for relation removal when Nexus exposes no remove action."""
    from unittest.mock import Mock

    mock_relation = {
        "_links": {"self": {"href": "test-update-url"}},
        "primaryOrganization": False,
    }

    original_get = nexus_manager.organisationer.nexus_client.get
    get_response = Mock()
    get_response.json.return_value = dict(mock_relation)
    nexus_manager.organisationer.nexus_client.get = Mock(return_value=get_response)

    try:
        result = nexus_manager.organisationer.fjern_borger_fra_organisation(
            mock_relation
        )

        assert result is False
        nexus_manager.organisationer.nexus_client.get.assert_called_once_with(
            "test-update-url"
        )
    finally:
        nexus_manager.organisationer.nexus_client.get = original_get


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


def test_hent_depotlister(nexus_manager: NexusClientManager):
    if not os.getenv("NEXUS_HCL_DEPOT_ORDER_FILTER_CONFIGURATION_IDS"):
        pytest.skip("NEXUS_HCL_DEPOT_ORDER_FILTER_CONFIGURATION_IDS is not configured")
    borgere = nexus_manager.organisationer.hent_borgere_med_udlåns_bestillinger()
    assert borgere is not None
    assert len(borgere) > 0


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeDepotOrderClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, endpoint: str) -> FakeResponse:
        self.calls.append(endpoint)
        match endpoint:
            case "/api/hcl-depot/orders?orderFilterConfigurationId=filter-1":
                return FakeResponse(
                    [
                        {"receiver": {"patientIdentifier": "131152-1105"}},
                        {"receiver": {"patientIdentifier": "1311521105"}},
                        {"receiver": {"patientIdentifier": "invalid"}},
                    ]
                )
            case "/api/hcl-depot/orders?orderFilterConfigurationId=filter-2":
                return FakeResponse(
                    [{"receiver": {"patientIdentifier": "130842-1004"}}]
                )
            case _:
                raise AssertionError(f"Unexpected endpoint: {endpoint}")


def test_hent_borgere_med_udlåns_bestillinger_uses_configured_filter_ids() -> None:
    client = FakeDepotOrderClient()
    organisationer = OrganisationerClient(
        client,
        hcl_depot_order_filter_configuration_ids=["filter-1", "filter-2"],
    )

    assert organisationer.hent_borgere_med_udlåns_bestillinger() == [
        "1311521105",
        "1308421004",
    ]
    assert client.calls == [
        "/api/hcl-depot/orders?orderFilterConfigurationId=filter-1",
        "/api/hcl-depot/orders?orderFilterConfigurationId=filter-2",
    ]


def test_hent_borgere_med_udlåns_bestillinger_without_filter_ids_does_not_call_api() -> (
    None
):
    client = FakeDepotOrderClient()
    organisationer = OrganisationerClient(client)

    assert organisationer.hent_borgere_med_udlåns_bestillinger() is None
    assert client.calls == []


def test_hcl_depot_orders_endpoint_is_instance_relative() -> None:
    assert hcl_depot_orders_endpoint("filter 1") == (
        "/api/hcl-depot/orders?orderFilterConfigurationId=filter+1"
    )


def test_fjern_medarbejder_fra_forløb(
    nexus_manager: NexusClientManager, test_borger: dict
):
    visning = nexus_manager.borgere.hent_visning(test_borger)
    assert visning is not None

    referencer = nexus_manager.borgere.hent_referencer(visning)
    assert referencer is not None

    medarbejdere = filter_by_path(
        referencer,
        "/Børn og Unge Grundforløb/Sag: Anbringelse/professionalReference",
        active_pathways_only=True,
    )

    if len(medarbejdere) == 0:
        pytest.skip(
            "Ingen medarbejdere fundet i forløb til test af fjern_medarbejder_fra_forløb"
        )

    succes = nexus_manager.organisationer.fjern_medarbejder_fra_forløb(medarbejdere[0])
    assert succes
