import pytest
import os

from dotenv import load_dotenv
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.functionality.borgere import BorgerClient
from kmd_nexus_client.functionality.organisationer import OrganisationerClient
from kmd_nexus_client.functionality.indsatser import IndsatsClient, GrantsClient
from kmd_nexus_client.functionality.opgaver import OpgaverClient
from kmd_nexus_client.functionality.kalender import KalenderClient
from kmd_nexus_client.functionality.forløb import ForløbClient

# Load environment variables from .env
load_dotenv()

@pytest.fixture(scope="session")
def nexus_manager():
    """Primary fixture - NexusClientManager provides access to all functionality clients."""
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    instance = os.getenv("INSTANCE")
    
    if not all([client_id, client_secret, instance]):
        raise ValueError("CLIENT_ID, CLIENT_SECRET, and INSTANCE must be set in .env file")
    
    return NexusClientManager(
        instance=instance,
        client_id=client_id,
        client_secret=client_secret,
    )

@pytest.fixture(scope="session")
def base_client(nexus_manager):
    """Legacy fixture - returns the underlying NexusClient for backward compatibility."""
    return nexus_manager.nexus_client

@pytest.fixture
def test_borger(nexus_manager: NexusClientManager):
    """Primary test citizen fixture using NexusClientManager."""
    return nexus_manager.borgere.hent_borger("0108589995")

# Legacy individual client fixtures for backward compatibility
@pytest.fixture
def borgere_client(nexus_manager: NexusClientManager):
    """Legacy fixture - use nexus_manager.borgere instead."""
    return nexus_manager.borgere

@pytest.fixture
def organisationer_client(nexus_manager: NexusClientManager):
    """Legacy fixture - use nexus_manager.organisationer instead."""
    return nexus_manager.organisationer

@pytest.fixture
def indsats_client(nexus_manager: NexusClientManager):
    """Legacy fixture - use nexus_manager.indsats instead."""
    return nexus_manager.indsats

@pytest.fixture  
def grants_client(nexus_manager: NexusClientManager):
    """Legacy fixture - use nexus_manager.grants instead."""
    return nexus_manager.grants

@pytest.fixture
def opgaver_client(nexus_manager: NexusClientManager):
    """Legacy fixture - use nexus_manager.opgaver instead."""
    return nexus_manager.opgaver

@pytest.fixture
def kalender_client(nexus_manager: NexusClientManager):
    """Legacy fixture - use nexus_manager.kalender instead."""
    return nexus_manager.kalender

@pytest.fixture
def forløb_client(nexus_manager: NexusClientManager):
    """Legacy fixture - use nexus_manager.forløb instead."""
    return nexus_manager.forløb