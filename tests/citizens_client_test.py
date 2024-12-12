import pytest

from .nexus_client_test import base_client  # noqa
from nexus_client.functionality.citizens import (
    CitizensClient,
    filter_pathway_references,
    filter_references,
)


@pytest.fixture
def citizens_client(base_client):
    return CitizensClient(base_client)


def test_get_citizen(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    assert citizen["patientIdentifier"]["identifier"] == "251248-9996"
    assert citizen["firstName"] == "Nancy"
    assert citizen["lastName"] == "Berggren"
    assert citizen["fullName"] == "Nancy Berggren"


def test_get_citizen_not_found(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2110010000")
    assert citizen is None


def test_get_citizen_preferences(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    preferences = citizens_client.get_citizen_preferences(citizen)
    assert preferences["CITIZEN_PATHWAY"] is not None
    assert len(preferences["CITIZEN_PATHWAY"]) > 0


def test_get_citizen_pathway(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    pathway = citizens_client.get_citizen_pathway(citizen)
    assert pathway["name"] == "- Alt"


def test_get_citizen_pathway_not_found(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    pathway = citizens_client.get_citizen_pathway(citizen, "Not a real pathway")
    assert pathway is None


def test_get_citizen_pathway_references(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)
    assert references is not None
    assert len(references) > 0


def test_filter_pathway_references(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)
    filtered = filter_pathway_references(
        references, lambda x: x["activityIdentifier"]["type"] == "PATIENT_PATHWAY"
    )
    assert filtered is not None
    assert len(filtered) > 0


def test_filter_references(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/*",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0


def test_filter_references_with_wildcard(citizens_client: CitizensClient):
    citizen = citizens_client.get_citizen("2512489996")
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0
    assert all("Medicin" in ref["name"] for ref in filtered)
