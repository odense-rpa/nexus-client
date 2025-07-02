import pytest
import os

from dotenv import load_dotenv
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.borgere import CitizensClient
from kmd_nexus_client.functionality.organisationer import OrganisationerClient
from kmd_nexus_client.functionality.indsatser import IndsatsClient, GrantsClient
from kmd_nexus_client.functionality.opgaver import OpgaverClient
from kmd_nexus_client.functionality.kalender import KalenderClient
from kmd_nexus_client.functionality.forløb import ForløbClient

# Load environment variables from .env
load_dotenv()

@pytest.fixture(scope="session")
def base_client():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    instance = os.getenv("INSTANCE")
    
    if not all([client_id, client_secret, instance]):
        raise ValueError("CLIENT_ID, CLIENT_SECRET, and INSTANCE must be set in .env file")
    
    return NexusClient(
        instance=instance,
        client_id=client_id,
        client_secret=client_secret,
    )

@pytest.fixture
def borgere_client(base_client):
    return CitizensClient(base_client)

@pytest.fixture
def test_citizen(borgere_client: CitizensClient):
    return borgere_client.get_citizen("0108589995")

@pytest.fixture
def organisationer_client(base_client):
    return OrganisationerClient(base_client)

@pytest.fixture
def grants_client(base_client):
    return GrantsClient(base_client)

@pytest.fixture
def indsats_client(base_client):
    return IndsatsClient(base_client)

@pytest.fixture
def opgaver_client(base_client):
    return OpgaverClient(base_client)

@pytest.fixture
def kalender_client(base_client):
    return KalenderClient(base_client)

@pytest.fixture
def forløb_client(base_client):
    return ForløbClient(base_client)