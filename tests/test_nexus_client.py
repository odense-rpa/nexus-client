# Fixtures are automatically loaded from conftest.py

def test_nexus_client_initialization(base_client):
    # Example test to verify initialization
    assert base_client.base_url.startswith("https://")
    assert "nexus.kmd.dk" in base_client.base_url
    
    assert base_client.api is not None
    assert "activeAssignments" in base_client.api