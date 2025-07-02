import pytest
import os

from dotenv import load_dotenv
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.borgere import CitizensClient
from kmd_nexus_client.functionality.organizations import OrganizationsClient
from kmd_nexus_client.functionality.grants import GrantsClient
from kmd_nexus_client.functionality.opgaver import OpgaverClient
from kmd_nexus_client.functionality.kalender import KalenderClient
from kmd_nexus_client.functionality.forløb import ForløbClient

# Load environment variables from .env
load_dotenv()

@pytest.fixture
def base_client(scope="session"):
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
def citizens_client(base_client): # noqa
    return CitizensClient(base_client)

@pytest.fixture
def test_citizen(citizens_client: CitizensClient):
    return citizens_client.get_citizen("0108589995")

@pytest.fixture
def organizations_client(base_client):
    return OrganizationsClient(base_client)

@pytest.fixture
def grants_client(base_client):
    return GrantsClient(base_client)

@pytest.fixture
def assignments_client(base_client):
    return OpgaverClient(base_client)

@pytest.fixture
def calendar_client(base_client):
    return KalenderClient(base_client)

@pytest.fixture
def cases_client(base_client):
    return ForløbClient(base_client)