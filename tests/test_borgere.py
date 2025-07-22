# Fixtures are automatically loaded from conftest.py

from kmd_nexus_client.manager import NexusClientManager

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

