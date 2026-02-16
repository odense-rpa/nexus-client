import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.tree_helpers import filter_by_predicate

def test_hent_borgers_skemaer(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente skemaer for en borger."""
    citizen = test_borger
    skemaer = nexus_manager.skemaer.hent_skemadefinition_uden_forløb(citizen)
    
    assert isinstance(skemaer, list)
    # Skemaer kan være tomme, så vi checker bare at det er en liste

def test_hent_skemadefinition_på_forløb(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente skemadefinitioner for en borger på et specifikt forløb."""
    citizen = test_borger
    grundforløb = "Sundhedsfagligt grundforløb"
    forløb = "FSIII"
    
    skema = nexus_manager.skemaer.hent_skemadefinition_på_forløb(
        borger=citizen,
        grundforløb=grundforløb,
        forløb=forløb,
    )
    
    assert isinstance(skema, list)

def test_opret_skema_på_borger_uden_forløb(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at oprette et skema på en borger uden forløb."""
    citizen = test_borger
    skema_data = {
        "Emne": "Test Skema fra python",
        "Tekst": "Dette er et test skema fra python.",
    }
    skema_navn = "Sagsnotat - Ældre"
    handling = "Låst"

    
    oprettet_skema = nexus_manager.skemaer.opret_komplet_skema(
        borger=citizen,
        data=skema_data,
        skematype_navn=skema_navn,
        handling_navn=handling
    )

    assert oprettet_skema is not None
    assert "id" in oprettet_skema
    assert oprettet_skema["formDefinition"]["title"] == skema_navn

def test_opret_skema_på_borger_på_forløb(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at oprette et skema på en borger på forløb."""
    citizen = test_borger
    grundforløb = "Sundhedsfagligt grundforløb"
    forløb = "FSIII"
    skema_data = {
        "Emne": "Test Skema fra python på forløb",
        "Tekst": "Dette er et test skema fra python på forløb.",
    }
    skema_navn = "Sagsnotat - Ældre"
    handling = "Låst"

    
    oprettet_skema = nexus_manager.skemaer.opret_komplet_skema(
        borger=citizen,
        grundforløb=grundforløb,
        forløb=forløb,
        data=skema_data,
        skematype_navn=skema_navn,
        handling_navn=handling
    )

    assert oprettet_skema is not None
    assert "id" in oprettet_skema
    assert oprettet_skema["formDefinition"]["title"] == skema_navn

def test_hent_skemareferencer(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente skemareferencer for en borger."""
    citizen = test_borger
    skemareferencer = nexus_manager.skemaer.hent_skemareferencer(borger=citizen)
    
    assert isinstance(skemareferencer, list)
    # Skemareferencer kan være tomme, så vi checker bare at det er en liste

def test_hent_skema_fra_reference(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente et skema fra en skemareference."""
    skemareferencer = nexus_manager.skemaer.hent_skemareferencer(borger=test_borger)

    # find selv et skema du vil bruge - 12345 virker næppe
    skemareference = next((ref for ref in skemareferencer if ref["Skemaid"] == 12345), None)
    skema = nexus_manager.skemaer.hent_skema_fra_reference(reference=skemareference)

    assert skema is not None
    assert "id" in skema
    assert skema["id"] == skemareference["id"]

def test_rediger_skema(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at redigere et eksisterende skema."""
        
    visning = nexus_manager.borgere.hent_visning(test_borger)
    assert visning is not None, "Visning should not be None"

    aktiviter = nexus_manager.borgere.hent_aktiviteter(visning=visning)
    skemaer = filter_by_predicate(
        aktiviter,
        lambda aktivitet: aktivitet.get("patientActivityType") == "formData"
    )
    skema = filter_by_predicate(
        skemaer,
        lambda skema: skema.get("id") == 10274229
    )

    skema = nexus_manager.skemaer.rediger_skema(
        skema=skema[0],
        handling_navn="Aktivt",
        data={
            "Navn": "Simon"
        },
    )    
    
    navn_felt = next((item for item in skema["items"] if item["label"] == "Navn"), None)
    assert navn_felt is not None, "Navn field should be present in the skema"
    assert navn_felt["value"] == "Simon", "Navn field should have value 'Simon'"

def test_hent_koordinator_skema_opret_netværksperson(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente koordinator skema og oprette netværksperson på borger."""
    citizen = test_borger    

    visning = nexus_manager.borgere.hent_visning(test_borger)
    assert visning is not None, "Visning should not be None"

    aktiviter = nexus_manager.borgere.hent_aktiviteter(visning=visning)
    skemaer = filter_by_predicate(
        aktiviter,
        lambda aktivitet: aktivitet.get("patientActivityType") == "formData"
    )
    skema = filter_by_predicate(
        skemaer,
        lambda skema: skema.get("id") == 10274229
    )

    skema = nexus_manager.hent_fra_reference(skema[0])
    
    assert skema is not None, "Koordinator skema should not be None"

    navn_felt = next((item for item in skema["items"] if item["label"] == "Navn"), None)
    organisationstilknytning_felt = next((item for item in skema["items"] if item["label"] == "Organisationstilknytning"), None)
    stillingsbetegnelse_felt = next((item for item in skema["items"] if item["label"] == "Stillingsbetegnelse"), None)

    if not navn_felt or not organisationstilknytning_felt or not stillingsbetegnelse_felt:
        pytest.fail("Der mangler udfyldte felter i koordinator skemaet")

    navn = navn_felt["value"]
    organisationstilknytning = organisationstilknytning_felt["value"]
    stillingsbetegnelse = stillingsbetegnelse_felt["value"]
    
    response_json = nexus_manager.borgere.opret_netværksperson(
        borger=citizen,
        netværksperson_data={
            "firstName": navn.split(" ")[0],
            "lastName": " ".join(navn.split(" ")[1:]),
            "relationDescription": f"Koordinator - {organisationstilknytning}",
            "title": stillingsbetegnelse,
        }
    )

    assert response_json is not None, "Response from opret_netværksperson should not be None"

    skema = nexus_manager.skemaer.rediger_skema(
        skema=skema,
        handling_navn="Inaktivt",
        data={},
    )

    assert skema is not None, "Skema should not be None after editing"


def test_skema_med_diagnose(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at håndtere skema med diagnosefelt."""
    citizen = test_borger
    skema_data = {
        "Diagnose": "DG041"
    }
    skema_navn = "Diagnose ICD-10"
    handling = "Aktivt"

    skema = nexus_manager.skemaer.opret_komplet_skema(
        borger=citizen,
        data=skema_data,
        skematype_navn=skema_navn,
        handling_navn=handling
    )

    assert skema is not None