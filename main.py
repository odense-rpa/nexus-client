import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from kmd_nexus_client import NexusClientManager

import json

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

borger = nexus.borgere.hent_borger("0108589995") or {}    # Falsk test-cpr nummer

visning = nexus.borgere.hent_visning(borger) or {}

# referencer = nexus.borgere.hent_referencer(visning)

# grant_refs = nexus.indsatser.filtrer_indsats_referencer(
#     referencer, kun_aktive=True, leverandør_navn="Testleverandør Supporten Dag"
# )

pass

