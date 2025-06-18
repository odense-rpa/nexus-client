import re

from typing import Optional
from httpx import HTTPStatusError
from typing import List, Callable

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.utils import sanitize_cpr

def filter_references(json_input: List[dict], path: str, active_pathways_only: bool):
    matches = re.findall(r'/([^/]+)+', path)

    if not matches:
        raise ValueError("Can't match empty path")

    filter_path = matches

    elements = []
    for item in json_input:
        elements.extend(_filter_tree(item, [], filter_path, active_pathways_only))

    return elements

def _filter_tree(root: dict, path: List[dict], filter_path: List[str], active_pathways_only: bool):
    result = []

    # Check here
    if (
        active_pathways_only 
        and root.get("type") == "patientPathwayReference" 
        and root.get("pathwayStatus") != "ACTIVE"
    ):
        return result

    path.append(root)

    if _compare_filter_and_path(path, filter_path):
        result.append(root)
    else:
        children = root.get("children")
        if children and len(filter_path) > len(path):
            for child in children:
                result.extend(_filter_tree(child, path, filter_path, active_pathways_only))

    path.pop()

    return result

def _compare_filter_and_path(path: List[dict], filter_path: List[str]):
    if len(path) != len(filter_path):
        return False

    for i in range(len(path)):
        name_match = (
            filter_path[i] == "*"
            or re.fullmatch(filter_path[i].replace('%', '.*'), path[i].get("name", "")) is not None
            or re.fullmatch(filter_path[i].replace('%', '.*'), path[i].get("type", "")) is not None
        )

        if not name_match:
            return False

    return True


def filter_pathway_references(references: List[dict], filter: Callable[[dict],bool]) -> List[dict]:
    """
    Filter a list of pathway references recursivly.
    :param references: The list of references to filter.
    :param filter: The filter function to apply.
    :return: The filtered list of references.
    """
    result = []
    
    for reference in references:
        if filter(reference):
            result.append(reference)
            
        if "children" in reference:
            result += filter_pathway_references(reference["children"], filter)
    
    return result  
    

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
    