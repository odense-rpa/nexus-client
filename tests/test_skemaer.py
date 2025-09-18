import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager

def test_hent_borgers_skemaer(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente skemaer for en borger."""
    citizen = test_borger
    skemaer = nexus_manager.skemaer.hent_tilgængelige_skematyper(citizen)
    
    assert isinstance(skemaer, list)
    # Skemaer kan være tomme, så vi checker bare at det er en liste

def test_opret_skema_på_borger(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at oprette et skema på en borger."""
    citizen = test_borger
    skema_data = {
        "Emne": "Test Skema fra python",
        "Tekst": "Dette er et test skema fra python.",
    }
    skema_navn = "Sagsnotat - Ældre"
    handling = "Låst"

    
    oprettet_skema = nexus_manager.skemaer.opret_komplet_skema(
        objekt=citizen,
        data=skema_data,
        skematype_navn=skema_navn,
        handling_navn=handling
    )

    assert oprettet_skema is not None
    assert "id" in oprettet_skema
    assert oprettet_skema["title"] == skema_data["title"]