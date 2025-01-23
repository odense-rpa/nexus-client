import os
from dotenv import load_dotenv

from kmd_nexus_client import NexusClient, CitizensClient, OrganizationsClient

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

#organizations = org_client.get_organizations()
#org_client.add_citizen_to_organization(res, "1234567890")
#org = [org for org in organizations if org["name"] == "Testorganisation Supporten Aften"][0]
#result = org_client.add_citizen_to_organization(citizen, org)

#organizations = org_client.get_organizations_by_citizen(citizen)
#org = [org for org in organizations if org["organization"]["name"] == "Testorganisation Supporten Aften"][0]
#org_client.remove_citizen_from_organization(org)

#print(org["_links"])
