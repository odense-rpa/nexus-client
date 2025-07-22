import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from kmd_nexus_client import NexusClientManager

import json

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

# borger = nexus.borgere.hent_borger("0108589995") or {}

# visning = nexus.borgere.hent_visning(borger) or {}

# referencer = nexus.borgere.hent_referencer(visning)

# grant_refs = nexus.indsats.filtrer_indsats_referencer(
#     referencer, kun_aktive=True, leverandør_navn="Testleverandør Supporten Dag"
# )


# print(len(grant_refs))
# for ref in grant_refs:
#     # full_grant = nexus.indsats.hent_indsats(ref)
#     print(ref["name"])
with open("grant-prototype.json", "r") as file:
    # Load the JSON data from the file
    grant_prototype = json.load(file)

    elements = grant_prototype.get("currentElements", [])
    max_length = max(len(element["type"]) for element in elements)
    
    print(f"{"Type".ljust(max_length)}\tDate\tText\tValue\tselectedValues\tpossibleValues\tDecimal")


    for element in elements:
        # Pad element type for alignment
        is_known = 'date' in element or 'text' in element or 'value' in element or 'selectedValues' in element or 'possibleValues' in element or 'decimal' in element

        if is_known:
            continue

        print(f"{element['type'].ljust(max_length)}\t{'date' in element}\t{'text' in element}\t{'value' in element}\t{'selectedValues' in element}\t\t{'possibleValues' in element}\t\t{'decimal' in element}")

