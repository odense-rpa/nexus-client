import os
import logging
from dotenv import load_dotenv

from kmd_nexus_client import NexusClientManager
from kmd_nexus_client.tree_helpers import filter_by_path


logging.basicConfig(level=logging.INFO)

load_dotenv()

client_id = os.getenv("CLIENT_ID") or ""
client_secret = os.getenv("CLIENT_SECRET") or ""
instance = os.getenv("INSTANCE") or ""

# Use NexusClientManager instead of individual clients
nexus = NexusClientManager(
    instance=instance,
    client_id=client_id,
    client_secret=client_secret,
)

borger = nexus.borgere.hent_borger("0104909989") or {}  # Falsk test-cpr nummer

visning = nexus.borgere.hent_visning(borger) or {}
referencer = nexus.borgere.hent_referencer(visning)

pass
