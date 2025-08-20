# Fixtures are automatically loaded from conftest.py

from kmd_nexus_client.manager import NexusClientManager

def test_hent_indbakke(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente MedCom indbakke for en borger."""
    citizen = test_borger
    indbakke = nexus_manager.medcom.hent_indbakke(citizen)
    
    assert indbakke is not None
    assert "totalItems" in indbakke
    assert "pages" in indbakke
    assert isinstance(indbakke["pages"], list)

def test_hent_alle_beskeder(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at hente alle MedCom beskeder for en borger."""
    citizen = test_borger
    beskeder = nexus_manager.medcom.hent_alle_beskeder(citizen)
    
    assert isinstance(beskeder, list)
    # Beskeder kan være tomme, så vi checker bare at det er en liste

def test_dekoder_medcom_xml(nexus_manager: NexusClientManager):
    """Test at dekode MedCom XML indhold."""
    # Mock besked med base64 encoded XML
    mock_besked = {
        "raw": "PGV4YW1wbGU+VGVzdCBYTUw8L2V4YW1wbGU+"  # Base64: <example>Test XML</example>
    }
    
    xml_indhold = nexus_manager.medcom.dekoder_medcom_xml(mock_besked)
    assert xml_indhold == "<example>Test XML</example>"

def test_dekoder_medcom_xml_ingen_raw(nexus_manager: NexusClientManager):
    """Test at dekode MedCom XML når der ikke er raw data."""
    mock_besked = {"subject": "Test besked"}
    
    xml_indhold = nexus_manager.medcom.dekoder_medcom_xml(mock_besked)
    assert xml_indhold is None

def test_filtrer_beskeder_efter_emne(nexus_manager: NexusClientManager):
    """Test filtrering af beskeder efter emne."""
    mock_beskeder = [
        {"subject": "Vigtig besked om behandling"},
        {"subject": "Almindelig besked"},
        {"subject": "Behandling resultat"}
    ]
    
    filtrerede = nexus_manager.medcom.filtrer_beskeder(
        mock_beskeder, 
        subject="behandling"
    )
    
    assert len(filtrerede) == 2
    assert all("behandling" in besked["subject"].lower() for besked in filtrerede)

def test_filtrer_beskeder_med_forloeb(nexus_manager: NexusClientManager):
    """Test filtrering af beskeder med forløb."""
    mock_beskeder = [
        {
            "subject": "Besked med forløb",
            "pathwayAssociation": {
                "placement": {"name": "MedCom", "programPathwayId": "123"}
            }
        },
        {"subject": "Besked uden forløb"},
        {
            "subject": "Anden besked med forløb", 
            "pathwayAssociation": {
                "placement": {"name": "Test", "programPathwayId": "456"}
            }
        }
    ]
    
    # Filtrer beskeder med forløb
    med_forloeb = nexus_manager.medcom.filtrer_beskeder(
        mock_beskeder, 
        har_forloeb=True
    )
    assert len(med_forloeb) == 2
    
    # Filtrer beskeder uden forløb
    uden_forloeb = nexus_manager.medcom.filtrer_beskeder(
        mock_beskeder, 
        har_forloeb=False
    )
    assert len(uden_forloeb) == 1

def test_get_besked_statistik(nexus_manager: NexusClientManager, test_borger: dict):
    """Test at få statistik for MedCom beskeder."""
    citizen = test_borger
    
    # Mock hent_alle_beskeder metoden
    mock_beskeder = [
        {
            "subject": "Besked 1",
            "pathwayAssociation": {
                "placement": {"name": "MedCom", "programPathwayId": "123"}
            }
        },
        {"subject": "Besked 2"},
        {
            "subject": "Besked 3",
            "pathwayAssociation": {
                "placement": {"name": "Test", "programPathwayId": "456"}
            }
        }
    ]
    
    # Temporarily replace the method
    original_method = nexus_manager.medcom.hent_alle_beskeder
    nexus_manager.medcom.hent_alle_beskeder = lambda x: mock_beskeder
    
    try:
        statistik = nexus_manager.medcom.get_besked_statistik(citizen)
        
        assert statistik["total_beskeder"] == 3
        assert statistik["med_forloeb"] == 2
        assert statistik["uden_forloeb"] == 1
        assert statistik["forloeb_fordeling"]["MedCom"] == 1
        assert statistik["forloeb_fordeling"]["Test"] == 1
    finally:
        # Restore original method
        nexus_manager.medcom.hent_alle_beskeder = original_method
