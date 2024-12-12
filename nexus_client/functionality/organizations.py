from nexus_client.client import NexusClient
from nexus_client.utils import sanitize_cpr


class OrganizationsClient():
    
    def __init__(self, nexus_client: NexusClient):
        self.nexus_client = nexus_client
        
        
    def get_organizations(self):
        """
        Get all organizations.
        
        :return: All organizations.
        """
        response = self.nexus_client.get(self.nexus_client.api["organizations"])
        return response.json()
    
    def get_organizations_by_citizen(self, citizen: dict):
        """
        Get all organizations by citizen.
        
        :param citizen: The citizen to retrieve organizations for.
        :return: All organizations by citizen.
        """
        response = self.nexus_client.get(citizen["_links"]["organizations"]["href"])
        return response.json()