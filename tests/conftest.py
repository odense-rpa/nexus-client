import pytest
import os

from dotenv import load_dotenv
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.tree_helpers import filter_by_path

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
    """Returns the underlying NexusClient."""
    return nexus_manager.nexus_client

@pytest.fixture
def test_borger(nexus_manager: NexusClientManager):
    """Primary test citizen fixture using NexusClientManager."""
    return nexus_manager.borgere.hent_borger("0108589995")

 
@pytest.fixture(scope="function")
def test_indsats(nexus_manager: NexusClientManager, test_borger: dict):
    visning = nexus_manager.borgere.hent_visning(test_borger)
    assert visning is not None, "Ingen visning fundet for test borger"

    references = nexus_manager.borgere.hent_referencer(visning)

    references = filter_by_path(
        references, path_pattern="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%"
    )

    assert len(references) > 0, "Ingen referencer fundet for test indsats"
    return nexus_manager.hent_fra_reference(references[0])  # Return the first reference for testing

