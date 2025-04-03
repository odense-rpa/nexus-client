import os
import logging
from dotenv import load_dotenv

from kmd_nexus_client import NexusClient, CitizensClient, OrganizationsClient

logging.basicConfig(level=logging.INFO)

load_dotenv(dotenv_path="env.local")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
instance = os.getenv("INSTANCE")


client = NexusClient(
        instance=instance,
        client_id=client_id,
        client_secret=client_secret,
    )

citizens_client = CitizensClient(client)
org_client = OrganizationsClient(client)

citizen = citizens_client.get_citizen("2512489996")
