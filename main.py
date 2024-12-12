import os
from dotenv import load_dotenv

from nexus_client import NexusClient, CitizensClient

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

res = citizens_client.get_citizen("2512489996")

print(res.json())
