from typing import Optional, List, Callable
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.utils import sanitize_cpr
from kmd_nexus_client.tree_helpers import filter_by_path, filter_by_predicate


def filter_references(json_input: List[dict], path: str, active_pathways_only: bool):
    """
    Filter pathway references by path pattern with wildcard support.
    
    DEPRECATED: Use tree_helpers.filter_by_path directly for new code.
    This function is maintained for backward compatibility.
    
    :param json_input: List of root nodes to search
    :param path: Path pattern like "/parent/child/*" or "/parent/child/name%"
    :param active_pathways_only: If True, skip inactive pathways
    :return: List of nodes matching the path pattern
    """
    return filter_by_path(json_input, path, active_pathways_only)


def filter_pathway_references(references: List[dict], filter: Callable[[dict], bool]) -> List[dict]:
    """
    Filter pathway references recursively using a predicate function.
    
    DEPRECATED: Use tree_helpers.filter_by_predicate directly for new code.
    This function is maintained for backward compatibility.
    
    :param references: The list of references to filter
    :param filter: The filter function to apply
    :return: The filtered list of references
    """
    return filter_by_predicate(references, filter)  
    

class CitizensClient:
    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def get_citizen(self, citizen_cpr: str) -> dict:
        """
        Get a citizen by CPR number.

        :param citizen_cpr: The CPR number of the citizen to retrieve.
        :return: The citizen details, or None if the citizen was not found.
        """
        cpr = sanitize_cpr(citizen_cpr)

        try:
            response = self.client.post(
                self.client.api["patientDetailsSearch"],
                json={"businessKey": cpr, "keyType": "CPR"},
            )

            data = response.json()

            if data["isPatientAccessible"] is False:
                return None

            return data["patient"]

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_citizen_preferences(self, citizen: dict) -> dict:
        """
        Get a citizen's preferences.

        :param citizen: The citizen to retrieve preferences for.
        :return: The citizen's preferences.
        """
        response = self.client.get(citizen["_links"]["patientPreferences"]["href"])
        return response.json()

    def get_citizen_pathway(self, citizen: dict, pathway_name: str = "- Alt") -> dict:
        """
        Get a citizen's pathway.

        :param citizen: The citizen to retrieve the pathway for.
        :return: The citizen's pathway.
        """
        preferences = self.get_citizen_preferences(citizen)
        
        for item in preferences["CITIZEN_PATHWAY"]:
            if item["name"] == pathway_name:
                return self.client.get(item["_links"]["self"]["href"]).json()

        return None

    def get_citizen_pathway_references(self, pathway: dict) -> dict:
        """
        Get a citizen's pathway references.

        :param pathway: The pathway to retrieve references for.
        :return: The pathway references.
        """
        return self.client.get(pathway["_links"]["pathwayReferences"]["href"]).json()

    def get_citizen_pathway_activities(self, pathway: dict) -> dict:
        """
        Get a citizen's pathway activities.

        :param pathway: The pathway to retrieve activities for.
        :return: The pathway activities.
        """
        return self.client.get(pathway["_links"]["patientActivities"]["href"]).json()

    def resolve_reference(self, reference: dict) -> dict:
        """
        Resolve a reference to a full object.

        :param reference: The reference to resolve.
        :return: The full object.
        """
        if "referencedObject" in reference["_links"]:
            return self.client.get(reference["_links"]["referencedObject"]["href"]).json()

        if "self" in reference["_links"]:
            return self.client.get(reference["_links"]["self"]["href"]).json()

        raise ValueError("Can't resolve reference, neither referencedObject nor self link found.")
        
    def get_citizen_lendings(self, citizen: dict) -> Optional[dict]:
        """
        Get a citizen's lendings.

        :param citizen: The citizen to retrieve lendings for.
        :return: The citizen's lendings, or None if no lending info is available.
        """
        if not isinstance(citizen, dict):
            return None

        lendings = citizen["_links"].get("lendings")
        if not isinstance(lendings, dict):
            return None

        return self.client.get(lendings["href"] + "&active=true").json()
    