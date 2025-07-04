# Fixtures are automatically loaded from conftest.py

from kmd_nexus_client.functionality.borgere import (
    BorgerClient,
    filter_pathway_references,
    filter_references,
)

def test_hent_borger(borgere_client: BorgerClient):
    citizen = borgere_client.hent_borger("2512489996")

    assert citizen is not None
    assert citizen["patientIdentifier"]["identifier"] == "251248-9996"
    assert citizen["firstName"] == "Nancy"
    assert citizen["lastName"] == "Berggren"
    assert citizen["fullName"] == "Nancy Berggren"

def test_hent_borger_ikke_fundet(borgere_client: BorgerClient):
    citizen = borgere_client.hent_borger("2110010000")
    assert citizen is None

def test_hent_præferencer(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    preferences = borgere_client.hent_præferencer(citizen)
    assert preferences["CITIZEN_PATHWAY"] is not None
    assert len(preferences["CITIZEN_PATHWAY"]) > 0

def test_hent_visning(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None
    assert pathway["name"] == "- Alt"

def test_hent_visning_ikke_fundet(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen, "Not a real pathway")
    assert pathway is None

def test_hent_referencer(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None

    references = borgere_client.hent_referencer(pathway)
    assert references is not None
    assert len(references) > 0

def test_filtrer_forløb_referencer(borgere_client: BorgerClient, test_borger):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None

    references = borgere_client.hent_referencer(pathway)
    filtered = filter_pathway_references(
        references, lambda x: x["activityIdentifier"]["type"] == "PATIENT_PATHWAY"
    )
    assert filtered is not None
    assert len(filtered) > 0

def test_filtrer_referencer(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None

    references = borgere_client.hent_referencer(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/*",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0

def test_filtrer_referencer_med_wildcard(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None

    references = borgere_client.hent_referencer(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0
    assert all("Medicin" in ref["name"] for ref in filtered)

def test_hent_fra_reference_forløb(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)

    assert pathway is not None

    references = borgere_client.hent_referencer(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = borgere_client.client.hent_fra_reference(references[0])

    assert resolved is not None
    assert resolved["name"] == references[0]["name"]
    
def test_hent_fra_reference_indsats(borgere_client: BorgerClient, test_borger: dict):
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)

    assert pathway is not None

    references = borgere_client.hent_referencer(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = borgere_client.client.hent_fra_reference(references[0])

    assert resolved is not None
    assert resolved["name"] == references[0]["name"]
    assert "currentElements" in resolved

# def test_hent_udlån(borgere_client: BorgerClient, test_borger: dict):
#     citizen = test_borger
#     lendings = borgere_client.hent_udlån(citizen)
#     assert lendings is not None
#     assert len(lendings) > 0
