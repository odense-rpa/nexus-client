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

    def hent_aktivitetsliste(
        self, navn: str, organisation: Optional[dict], medarbejder: Optional[dict], antal_sider: int = 50
    ) -> list[dict] | None:
        
        præferencer = self.client.get("preferences").json()
        aktivitetsliste = next(
            (item for item in præferencer.get("ACTIVITY_LIST", []) if item.get("name") == navn),
            None
        )
        
        if not aktivitetsliste:
            return None

        aktivitetsliste = self.client.get(aktivitetsliste["_links"]["self"]["href"]).json()
        base_content_url = aktivitetsliste["_links"]["content"]["href"]

        # FIXED: correct ordering
        if organisation and medarbejder:
            content_url = (base_content_url +
                        f"&pageSize={antal_sider}"
                        f"&assignmentOrganizationAssignee={organisation['id']}"
                        f"&assignmentProfessionalAssignee={medarbejder['id']}")
        elif organisation:
            content_url = (base_content_url +
                        f"&pageSize={antal_sider}"
                        f"&assignmentOrganizationAssignee={organisation['id']}"
                        f"&assignmentProfessionalAssignee=NO_PROFESSIONAL_CRITERIA")
        elif medarbejder:
            content_url = (base_content_url +
                        f"&pageSize={antal_sider}"
                        f"&assignmentOrganizationAssignee=ALL_ORGANIZATIONS"
                        f"&assignmentProfessionalAssignee={medarbejder['id']}")
        else:
            content_url = (base_content_url +
                        f"&pageSize={antal_sider}"
                        f"&assignmentOrganizationAssignee=ALL_ORGANIZATIONS"
                        f"&assignmentProfessionalAssignee=NO_PROFESSIONAL_CRITERIA")

        activities_list = []

        # Removed try/except, unless you want custom error handling
        response = self.client.get(content_url)
        activities_data = response.json()

        pages = activities_data.get("pages", [])

        for i, page in enumerate(pages):
            if i >= antal_sider:
                break

            temp_activity = self.client.get(page["_links"]["content"]["href"]).json()

            if isinstance(temp_activity, list):
                for activity in temp_activity:
                    if isinstance(activity, dict) and "id" in activity:
                        activities_list.append(activity)

        return activities_list