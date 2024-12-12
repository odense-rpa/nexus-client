import os
import pytest
from dotenv import load_dotenv
from nexus_client.client import NexusClient

# Load environment variables from env.local
load_dotenv(dotenv_path="env.local")

@pytest.fixture
def base_client():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    instance = os.getenv("INSTANCE")
    
    if not all([client_id, client_secret, instance]):
        raise ValueError("CLIENT_ID, CLIENT_SECRET, and INSTANCE must be set in env.local")
    
    return NexusClient(
        instance=instance,
        client_id=client_id,
        client_secret=client_secret,
    )

def test_nexus_client_initialization(base_client):
    # Example test to verify initialization
    assert base_client.base_url.startswith("https://")
    assert "nexus.kmd.dk" in base_client.base_url
    
    assert base_client.api is not None
    assert "activeAssignments" in base_client.api
    
    
