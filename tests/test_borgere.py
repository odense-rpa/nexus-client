# Fixtures are automatically loaded from conftest.py

from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.functionality.borgere import (
    filter_pathway_references,
    filter_references,
)

def test_hent_borger(nexus_manager: NexusClientManager):
    citizen = nexus_manager.borgere.hent_borger("2512489996")

    assert citizen is not None
    assert citizen["patientIdentifier"]["identifier"] == "251248-9996"
    assert citizen["firstName"] == "Nancy"
    assert citizen["lastName"] == "Berggren"
    assert citizen["fullName"] == "Nancy Berggren"

def test_hent_borger_ikke_fundet(nexus_manager: NexusClientManager):
    citizen = nexus_manager.borgere.hent_borger("2110010000")
    assert citizen is None

def test_hent_præferencer(nexus_manager: NexusClientManager, test_borger: dict):
    citizen = test_borger
    preferences = nexus_manager.borgere.hent_præferencer(citizen)
    assert preferences["CITIZEN_PATHWAY"] is not None
    assert len(preferences["CITIZEN_PATHWAY"]) > 0

def test_hent_visning(nexus_manager: NexusClientManager, test_borger: dict):
    citizen = test_borger
    pathway = nexus_manager.borgere.hent_visning(citizen)
    assert pathway is not None
    assert pathway["name"] == "- Alt"

def test_hent_visning_ikke_fundet(nexus_manager: NexusClientManager, test_borger: dict):
    citizen = test_borger
    pathway = nexus_manager.borgere.hent_visning(citizen, "Not a real pathway")
    assert pathway is None

def test_hent_referencer(nexus_manager: NexusClientManager, test_borger: dict):
    citizen = test_borger
    pathway = nexus_manager.borgere.hent_visning(citizen)
    assert pathway is not None

    references = nexus_manager.borgere.hent_referencer(pathway)
    assert references is not None
    assert len(references) > 0

def test_filtrer_forløb_referencer(nexus_manager: NexusClientManager, test_borger):
    citizen = test_borger
    pathway = nexus_manager.borgere.hent_visning(citizen)
    assert pathway is not None

    references = nexus_manager.borgere.hent_referencer(pathway)
    filtered = filter_pathway_references(
        references, lambda x: x["activityIdentifier"]["type"] == "PATIENT_PATHWAY"
    )
    assert filtered is not None
    assert len(filtered) > 0

def test_filtrer_referencer(nexus_manager: NexusClientManager, test_borger: dict):
    citizen = test_borger
    pathway = nexus_manager.borgere.hent_visning(citizen)
    assert pathway is not None

    references = nexus_manager.borgere.hent_referencer(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/*",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0

def test_filtrer_referencer_med_wildcard(nexus_manager: NexusClientManager, test_borger: dict):
    citizen = test_borger
    pathway = nexus_manager.borgere.hent_visning(citizen)
    assert pathway is not None

    references = nexus_manager.borgere.hent_referencer(pathway)
    filtered = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )
    assert filtered is not None
    assert len(filtered) > 0
    assert all("Medicin" in ref["name"] for ref in filtered)

def test_hent_fra_reference_forløb(nexus_manager: NexusClientManager, test_borger: dict):
    citizen = test_borger
    pathway = nexus_manager.borgere.hent_visning(citizen)

    assert pathway is not None

    references = nexus_manager.borgere.hent_referencer(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = nexus_manager.hent_fra_reference(references[0])

    assert resolved is not None
    assert resolved["name"] == references[0]["name"]
    
def test_hent_fra_reference_indsats(nexus_manager: NexusClientManager, test_borger: dict):
    pathway = nexus_manager.borgere.hent_visning(test_borger)

    assert pathway is not None

    references = nexus_manager.borgere.hent_referencer(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = nexus_manager.hent_fra_reference(references[0])

    assert resolved is not None
    assert resolved["name"] == references[0]["name"]
    assert "currentElements" in resolved

