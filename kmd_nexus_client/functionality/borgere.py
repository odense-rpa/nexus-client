from typing import Optional, List
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.utils import sanitize_cpr


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

    def hent_visning(
        self, borger: dict, visnings_navn: str = "- Alt"
    ) -> Optional[dict]:
        """
        Hent en visning for borgeren.

        :param borger: Borgeren der skal hentes visning for.
        :param visnings_navn: Navnet på visningen (standard: "- Alt").
        :return: Borgerens visning, eller None hvis visningen ikke findes.
        """
        preferences = self.hent_præferencer(borger=borger)

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

    # TODO: Overvej en funktion der kan hente en enkelt reference i en visning og resolve den med det samme.

    def hent_aktiviteter(self, visning: dict) -> List[dict]:
        """
        Hent aktiviteter fra en borgervisning (flad liste med tilstande, organisationer, medicinkort osv.).

        :param visning: Visningen der skal hentes aktiviteter for.
        :return: Patient aktiviteterne som flad liste.
        """
        return self.client.get(visning["_links"]["patientActivities"]["href"]).json()

    def hent_udlån(self, borger: dict) -> List[dict]|None:
        """
        Hent borgerens udlån.

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
        :return: Liste af aktive forløb som direkte objekter. De kan ikke anvendes direkte i andre funktioner. Brug istedet hent_visning til at få referencer.
        """
        return self.client.get(borger["_links"]["activePrograms"]["href"]).json()

    def opret_borger(self, borger_cpr: str) -> dict|None:
        """
        Opret en ny borger i KMD Nexus.

        :param borger_data: Data for den nye borger.
        :param cpr: CPR nummeret på borgeren der skal oprettes.
        :return: Det oprettede borgerobjekt.
        """
        
        cpr = sanitize_cpr(borger_cpr)

        try:
            prototype_response = self.client.get(
                f"{self.client.api["patients"]}/prototypeBasedOnCprSystem?cpr={cpr}"                
            )

            if prototype_response.status_code != 200:
                raise ValueError("Kan ikke hente prototype for borger.")

            prototype = prototype_response.json()

            response = self.client.post(
                self.client.api["patients"],
                json=prototype,
            )

            return response.json()

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise        
       
    def aktiver_borger_fra_kladde(self, borger: dict) -> dict:
        """
        Gemmer en borger fra status kladde uden ændringer, hvilket "aktiverer" borgeren i Nexus.

        :param borger: Borgeren der skal opdateres.        
        :return: Det opdaterede borgerobjekt.
        """

        prototype = self.client.get(borger["_links"]["self"]["href"]).json()
        
        if not prototype:
            raise ValueError("Kan ikke hente borgerens nuværende data.")

        response = self.client.put(
            borger["_links"]["update"]["href"],
            json=prototype,
        )

        return response.json()