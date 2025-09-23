import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager

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
    skema_navn = "Sagsnotat - Ældre"
    
    skema = nexus_manager.skemaer.hent_skemadefinition_på_forløb(
        objekt=citizen,
        grundforløb=grundforløb,
        forløb=forløb,
        skema_navn=skema_navn
    )
    
    assert isinstance(skema, dict)
    assert skema["title"] == skema_navn

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