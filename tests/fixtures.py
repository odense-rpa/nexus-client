import pytest
import os
from dotenv import load_dotenv

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.citizens import CitizensClient
from kmd_nexus_client.functionality.organizations import OrganizationsClient

# Load environment variables from env.local
load_dotenv(dotenv_path="env.local")


@pytest.fixture
def base_client(scope="session"):
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


@pytest.fixture
def citizens_client(base_client): # noqa
    return CitizensClient(base_client)

@pytest.fixture
def test_citizen(citizens_client: CitizensClient):
    return citizens_client.get_citizen("2512489996")


@pytest.fixture
def organizations_client(base_client):
    return OrganizationsClient(base_client)
