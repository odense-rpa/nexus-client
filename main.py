import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from kmd_nexus_client import (
    NexusClient,
    BorgerClient,
    OrganizationsClient,
    GrantsClient,
)

logging.basicConfig(level=logging.INFO)

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
instance = os.getenv("INSTANCE")


client = NexusClient(
    instance=instance,
    client_id=client_id,
    client_secret=client_secret,
)

borgere_client = BorgerClient(client)
org_client = OrganizationsClient(client)
grants = GrantsClient(client)

borger = borgere_client.hent_borger("0108589995")

grant_refs = grants.get_grant_references(borger)

#grant_refs = grants.filter_grant_references(grant_refs, True)
print(len(grant_refs))
for ref in grant_refs:
    full_grant = grants.get_grant(ref)

    print(full_grant["name"])
