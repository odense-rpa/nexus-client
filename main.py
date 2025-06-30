import os
import logging
from dotenv import load_dotenv
from datetime import datetime

from kmd_nexus_client import (
    NexusClient,
    CitizensClient,
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

citizens_client = CitizensClient(client)
org_client = OrganizationsClient(client)
grants = GrantsClient(client)

citizen = citizens_client.get_citizen("0108589995")

grants.create_grant(
    citizen=citizen,
    grundforløb="Sundhedsfagligt grundforløb",
    forløb="FSIII",
    indsats="Genoptræning basal genoptræning (SUL § 140)",
    leverandør="Testleverandør Supporten Dag",
    oprettelsesform="Tildel, Bestil",
    felter={"orderedDate": datetime.today(),"entryDate": datetime.today()},
    indsatsnote="",
)
