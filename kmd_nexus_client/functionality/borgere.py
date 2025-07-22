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
    

class BorgerClient:
    """
    Klient til borger-operationer i KMD Nexus.
    
    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.borgere.hent_borger(...)
    """
    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def hent_borger(self, borger_cpr: str) -> Optional[dict]:
        """
        Hent en borger via CPR nummer.

        :param borger_cpr: CPR nummeret på borgeren der skal hentes.
        :return: Borgerens detaljer, eller None hvis borgeren ikke blev fundet.
        """
        cpr = sanitize_cpr(borger_cpr)

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

    def hent_præferencer(self, borger: dict) -> dict:
        """
        Hent præferencer for borgeren.

        :param borger: Borgeren der skal hentes præferencer for.
        :return: Borgerens præferencer.
        """
        response = self.client.get(borger["_links"]["patientPreferences"]["href"])
        return response.json()

    def hent_visning(self, borger: dict, visnings_navn: str = "- Alt") -> Optional[dict]:
        """
        Hent en visning for borgeren.

        :param borger: Borgeren der skal hentes visning for.
        :param visnings_navn: Navnet på visningen (standard: "- Alt").
        :return: Borgerens visning, eller None hvis visningen ikke findes.
        """
        preferences = self.hent_præferencer(borger)
        
        for item in preferences["CITIZEN_PATHWAY"]:
            if item["name"] == visnings_navn:
                return self.client.get(item["_links"]["self"]["href"]).json()

        return None

    def hent_referencer(self, visning: dict) -> List[dict]:
        """
        Hent forløbsreferencer fra en borgervisning.

        :param visning: Visningen der skal hentes referencer for.
        :return: Forløbsreferencerne.
        """
        return self.client.get(visning["_links"]["pathwayReferences"]["href"]).json()

    def hent_aktiviteter(self, visning: dict) -> List[dict]:
        """
        Hent aktiviteter fra en borgervisning (flad liste med tilstande, organisationer, medicinkort osv.).

        :param visning: Visningen der skal hentes aktiviteter for.
        :return: Patient aktiviteterne som flad liste.
        """
        return self.client.get(visning["_links"]["patientActivities"]["href"]).json()

        
    def hent_udlån(self, borger: dict) -> Optional[dict]:
        """
        Hent borgerens udlån.

        TODO: Kontroller returtype - virker forkert

        :param borger: Borgeren der skal hentes udlån for.
        :return: Borgerens udlån, eller None hvis ingen udlån er tilgængelige.
        """
        if not isinstance(borger, dict):
            return None

        lendings = borger["_links"].get("lendings")
        if not isinstance(lendings, dict):
            return None

        return self.client.get(lendings["href"] + "&active=true").json()

    def hent_aktive_forløb(self, borger: dict) -> list:
        """
        Hent aktive forløb direkte via activePrograms link.

        :param borger: Borgeren der skal hentes aktive forløb for.
        :return: Liste af aktive forløb som direkte objekter.
        """
        return self.client.get(borger["_links"]["activePrograms"]["href"]).json()

    def find_reference(self, referencer: list, reference_navn: str, kun_aktive: bool = True) -> Optional[dict]:
        """
        Find en specifik reference rekursivt i reference-hierarkiet.

        :param referencer: Listen af referencer der skal søges i.
        :param reference_navn: Navnet på referencen der skal findes.
        :param kun_aktive: Kun find aktive forløb (standard: True).
        :return: Den fundne reference eller None hvis ikke fundet.
        """
        for ref in referencer:
            # Check om dette er den ønskede reference
            if ref.get("name") == reference_navn:
                if not kun_aktive or ref.get("pathwayStatus") == "ACTIVE":
                    return ref
            
            # Søg rekursivt i children
            if "children" in ref and ref["children"]:
                found = self.find_reference(ref["children"], reference_navn, kun_aktive)
                if found:
                    return found
        return None

    