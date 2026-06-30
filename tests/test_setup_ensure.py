from typing import Any

import pytest

from kmd_nexus_client.functionality.forloeb import ForløbClient
from kmd_nexus_client.functionality.organisationer import OrganisationerClient


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self.payload


class FakeNexusClient:
    def __init__(self) -> None:
        self.api = {"organizations": "organizations"}
        self.gets: list[str] = []
        self.puts: list[tuple[str, Any]] = []
        self.organisations = [
            {"id": 44, "name": "Hjælpemidler"},
            {"id": 317, "name": "Hjælpemidler og Genoptræning"},
        ]
        self.relations: list[dict[str, Any]] = []
        self.available_associations: list[dict[str, Any]] = []
        self.pathway_details: dict[str, dict[str, Any]] = {}

    def get(self, endpoint: str, **kwargs: Any) -> FakeResponse:
        self.gets.append(endpoint)
        if endpoint == "organizations":
            return FakeResponse(self.organisations)
        if endpoint == "patient-organizations":
            return FakeResponse(self.relations)
        if endpoint == "available-associations":
            return FakeResponse(self.available_associations)
        if endpoint in self.pathway_details:
            return FakeResponse(self.pathway_details[endpoint])
        return FakeResponse([])

    def put(self, endpoint: str, json: Any, **kwargs: Any) -> FakeResponse:
        self.puts.append((endpoint, json))
        if endpoint == "patient-organizations/317":
            relation = {
                "organization": {"id": 317, "name": "Hjælpemidler og Genoptræning"},
                "_links": {"self": {"href": "relation-317"}},
                "effectiveAtPresent": True,
            }
            self.relations.append(relation)
        if endpoint == "enroll-sag":
            return FakeResponse(
                {
                    "name": "Sag: Hjælpemidler anden myndighed",
                    "_links": {"selfReference": {"href": "sag-reference"}},
                },
                status_code=200,
            )
        return FakeResponse({}, status_code=200)


def make_borger() -> dict[str, Any]:
    return {
        "_links": {
            "patientOrganizations": {"href": "patient-organizations"},
            "availablePathwayAssociation": {"href": "available-associations"},
        }
    }


def test_organisation_lookup_normalizes_case_and_whitespace() -> None:
    client = FakeNexusClient()
    organisations = OrganisationerClient(client)  # type: ignore[arg-type]

    organisation = organisations.hent_organisation_ved_navn(
        "  hjælpemidler og genoptræning "
    )

    assert organisation is not None
    assert organisation["id"] == 317


def test_ensure_organisation_relation_reuses_existing_relation() -> None:
    client = FakeNexusClient()
    client.relations = [
        {
            "organization": {"id": 317, "name": "Hjælpemidler og Genoptræning"},
            "effectiveAtPresent": True,
        }
    ]
    organisations = OrganisationerClient(client)  # type: ignore[arg-type]

    result = organisations.sikr_borger_i_organisation(
        make_borger(), "hjælpemidler og genoptræning"
    )

    assert not result.created
    assert result.relation["organization"]["id"] == 317
    assert client.puts == []


def test_ensure_organisation_relation_creates_missing_relation() -> None:
    client = FakeNexusClient()
    organisations = OrganisationerClient(client)  # type: ignore[arg-type]

    result = organisations.sikr_borger_i_organisation(
        make_borger(), "hjælpemidler og genoptræning"
    )

    assert result.created
    assert result.relation["organization"]["id"] == 317
    assert client.puts == [("patient-organizations/317", "")]


def test_ensure_organisation_relation_fails_when_master_data_is_missing() -> None:
    client = FakeNexusClient()
    organisations = OrganisationerClient(client)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Nexus organisation not found"):
        organisations.sikr_borger_i_organisation(make_borger(), "Ukendt organisation")


def test_ensure_pathway_accepts_existing_udlaan_association() -> None:
    client = FakeNexusClient()
    client.available_associations = [
        {
            "name": "Udlån",
            "pathwayStatus": "ACTIVE",
            "_links": {"self": {"href": "udlaan-reference"}},
        }
    ]
    pathways = ForløbClient(client)  # type: ignore[arg-type]

    result = pathways.sikr_forløb(make_borger(), "Sundhedslogistik", "Udlån")

    assert not result.created
    assert result.case is not None
    assert result.case["name"] == "Udlån"
    assert client.puts == []


def test_ensure_pathway_creates_missing_child_when_parent_exists() -> None:
    client = FakeNexusClient()
    client.available_associations = [
        {
            "name": "Sundhedsfagligt Grundforløb",
            "pathwayStatus": "ACTIVE",
            "_links": {"self": {"href": "base-reference"}},
        }
    ]
    client.pathway_details = {
        "base-reference": {
            "name": "Sundhedsfagligt Grundforløb",
            "_links": {
                "activePrograms": {"href": "base-active-programs"},
                "availableNestedProgramPathways": {"href": "base-nested-pathways"},
            },
        },
        "base-active-programs": [],
        "base-nested-pathways": [
            {
                "name": "Sag: Hjælpemidler anden myndighed",
                "_links": {"enroll": {"href": "enroll-sag"}},
            }
        ],
    }
    pathways = ForløbClient(client)  # type: ignore[arg-type]

    result = pathways.sikr_forløb(
        make_borger(),
        "Sundhedsfagligt Grundforløb",
        "Sag: Hjælpemidler anden myndighed",
    )

    assert result.created
    assert result.case is not None
    assert result.case["name"] == "Sag: Hjælpemidler anden myndighed"
    assert client.puts == [("enroll-sag", {})]
