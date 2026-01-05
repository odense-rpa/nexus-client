from kmd_nexus_client.manager import NexusClientManager


def test_hent_tilstande(nexus_manager: NexusClientManager, test_borger: dict):

    assert "patientConditions" in test_borger["_links"]

    # Test the actual method
    tilstande = nexus_manager.tilstande.hent_tilstande(test_borger)

    # Should not raise an exception and should return valid response
    assert isinstance(tilstande, list)
    assert all(isinstance(t, dict) for t in tilstande)

def test_hent_tilstandstyper(nexus_manager: NexusClientManager, test_borger: dict):
    
    assert "availableConditionClassifications" in test_borger["_links"]

    # Test the actual method
    tilstandstyper = nexus_manager.tilstande.hent_tilstandstyper(test_borger)

    # Should not raise an exception and should return valid response
    assert isinstance(tilstandstyper, list)
    assert len(tilstandstyper) > 0
    assert all(isinstance(t, dict) for t in tilstandstyper)

def test_opret_tilstand(nexus_manager: NexusClientManager, test_borger: dict):

    tilstandstyper = nexus_manager.tilstande.hent_tilstandstyper(test_borger)
    assert len(tilstandstyper) > 0

    tilstandstype = [t for t in tilstandstyper if t["name"]=="Energi og handlekraft" and t["klMappingCode"]=="J4.6"][0]

    # Test the actual method
    ny_tilstand = nexus_manager.tilstande.opret_tilstand(test_borger, tilstandstype)

    # Should not raise an exception and should return valid response
    assert isinstance(ny_tilstand, dict)
