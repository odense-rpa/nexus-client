from typing import Optional 
from kmd_nexus_client.client import NexusClient


class AktivitetslisteClient:
    """
    Klient til aktivitetsliste-operationer i KMD Nexus.

    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.aktivitetslister.hent_aktivitetsliste(...)
    """

    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def hent_aktivitetsliste(self, navn: str, organisation: Optional[dict], medarbejder: Optional[dict], antal_sider: int = 50) -> list[dict] | None:
        """
        Fetch activities from Nexus API and return them as a list of dictionaries.

        Returns:
            Dictionary of activities keyed by activity ID
        """
        
        præferencer = self.client.get("preferences").json()        
        aktivitetsliste = next((item for item in præferencer.get("ACTIVITY_LIST", []) if item.get("name") == navn), None)
        
        if not aktivitetsliste:
            return None
        
        aktivitetsliste = self.client.get(aktivitetsliste["_links"]["self"]["href"]).json()

        base_content_url = aktivitetsliste["_links"]["content"]["href"]

        if organisation:
            content_url = base_content_url + f"&pageSize={antal_sider}&assignmentOrganizationAssignee={organisation['id']}&assignmentProfessionalAssignee=NO_PROFESSIONAL_CRITERIA"
        elif medarbejder:
            content_url = base_content_url + f"&pageSize={antal_sider}&assignmentOrganizationAssignee=ALL_ORGANIZATIONS&assignmentProfessionalAssignee={medarbejder['id']}"
        elif organisation and medarbejder:
            content_url = base_content_url + f"&pageSize={antal_sider}&assignmentOrganizationAssignee={organisation['id']}&assignmentProfessionalAssignee={medarbejder['id']}"
        else:
            content_url = base_content_url + f"&pageSize={antal_sider}&assignmentOrganizationAssignee=ALL_ORGANIZATIONS&assignmentProfessionalAssignee=NO_PROFESSIONAL_CRITERIA"

        activities_dict = []  # Initialize the dictionary to store activities

        try:
            response = self.client.get(content_url)
            activities_data = response.json()
            pages = activities_data["pages"]
            j = 0            
            
            for page in pages:
                temp_activity = self.client.get(page["_links"]["content"]["href"]).json()

                # Handle the case where temp_activity is a list of activities
                if isinstance(temp_activity, list):
                    for activity in temp_activity:
                        if isinstance(activity, dict) and "id" in activity:
                            activities_dict.append(activity)

                j += 1

                if j >= antal_sider or j == len(pages):
                    return activities_dict            
            
        except Exception:            
            raise