import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from kmd_nexus_client import NexusClientManager

logging.basicConfig(level=logging.INFO)

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
instance = os.getenv("INSTANCE")

# Use NexusClientManager instead of individual clients
nexus = NexusClientManager(
    instance=instance,
    client_id=client_id,
    client_secret=client_secret,
)
#TODO enable_ai_safety flag virker ikke på NexusClientManager. Fix eller fjern?

borger = nexus.borgere.hent_borger("0108589995")


grant_refs = nexus.indsats.hent_indsatser_referencer(borger)

print(len(grant_refs))
for ref in grant_refs:
    full_grant = nexus.indsats.hent_indsats(ref)
    print(full_grant["name"])
