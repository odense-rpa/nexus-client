# Fixtures are automatically loaded from conftest.py

from kmd_nexus_client.functionality.borgere import (
    CitizensClient,
    filter_pathway_references,
    filter_references,
)

def test_get_citizen(borgere_client: CitizensClient):
    citizen = borgere_client.get_citizen("2512489996")

    assert citizen is not None
    assert citizen["patientIdentifier"]["identifier"] == "251248-9996"
    assert citizen["firstName"] == "Nancy"
    assert citizen["lastName"] == "Berggren"
    assert citizen["fullName"] == "Nancy Berggren"

def test_get_citizen_not_found(borgere_client: CitizensClient):
    citizen = borgere_client.get_citizen("2110010000")
    assert citizen is None

def test_get_citizen_preferences(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    preferences = borgere_client.get_citizen_preferences(citizen)
    assert preferences["CITIZEN_PATHWAY"] is not None
    assert len(preferences["CITIZEN_PATHWAY"]) > 0

def test_get_citizen_pathway(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)
    assert pathway is not None
    assert pathway["name"] == "- Alt"

def test_get_citizen_pathway_not_found(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen, "Not a real pathway")
    assert pathway is None

def test_get_citizen_pathway_references(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)
    assert pathway is not None

    references = borgere_client.get_citizen_pathway_references(pathway)
    assert references is not None
    assert len(references) > 0

def test_filter_pathway_references(borgere_client: CitizensClient, test_citizen):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)
    assert pathway is not None

    references = borgere_client.get_citizen_pathway_references(pathway)
    filtered = filter_pathway_references(
        references, lambda x: x["activityIdentifier"]["type"] == "PATIENT_PATHWAY"
    )
    assert filtered is not None
    assert len(filtered) > 0

def test_filter_references(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)
    assert pathway is not None

    references = borgere_client.get_citizen_pathway_references(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/*",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0

def test_filter_references_with_wildcard(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)
    assert pathway is not None

    references = borgere_client.get_citizen_pathway_references(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0
    assert all("Medicin" in ref["name"] for ref in filtered)

def test_resolve_reference_pathway(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)

    assert pathway is not None

    references = borgere_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = borgere_client.resolve_reference(references[0])

    assert resolved is not None
    assert resolved["name"] == references[0]["name"]
    
def test_resolve_reference_grant(borgere_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)

    assert pathway is not None

    references = borgere_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = borgere_client.resolve_reference(references[0])

    assert resolved is not None
    assert resolved["name"] == references[0]["name"]
    assert "currentElements" in resolved

# def test_get_citizen_lendings(borgere_client: CitizensClient, test_citizen: dict):
#     citizen = test_citizen
#     lendings = borgere_client.get_citizen_lendings(citizen)
#     assert lendings is not None
#     assert len(lendings) > 0
