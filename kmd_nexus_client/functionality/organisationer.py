from typing import List
from datetime import date
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient


class OrganisationerClient:
    """
    Klient til håndtering af organisationer i KMD Nexus.
    
    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.organisationer.hent_organisation(...)
    
    Danske funktioner:
    - hent_organisationer() -> List[dict]
    - hent_leverandører() -> List[dict]
    - hent_organisation_ved_navn(navn) -> dict
    - hent_organisationer_for_borger(borger, kun_aktive=True) -> List[dict]
    - hent_borgere_for_organisation(organisation) -> List[dict]
    - hent_medarbejder_ved_initialer(initialer) -> dict
    - hent_medarbejdere_for_organisation(organisation) -> List[dict]
    - tilføj_borger_til_organisation(borger, organisation) -> bool
    - fjern_borger_fra_organisation(organisations_relation) -> bool
    - opdater_borger_organisations_relation(relation, slut_dato, primær_organisation) -> bool
    - opdater_leverandør(opdateret_leverandør) -> dict
    """
    
    def __init__(self, nexus_client: NexusClient):
        self.nexus_client = nexus_client

    def hent_organisationer(self) -> List[dict]:
        """
        Hent alle organisationer.

        :return: Alle organisationer.
        """
        response = self.nexus_client.get(self.nexus_client.api["organizations"])
        return response.json()
    
    def hent_leverandører(self) -> List[dict]:
        """
        Hent alle leverandører.

        :return: Alle leverandører.
        """
        response = self.nexus_client.get(self.nexus_client.api["suppliers"])
        return response.json()
    
    def hent_organisation_ved_navn(self, navn: str) -> dict:
        """
        Hent organisation ved navn.

        :param navn: Navnet på organisationen der skal hentes.
        :return: Organisationen.
        """
        organisationer = self.hent_organisationer()
        return [org for org in organisationer if org["name"] == navn][0]

    def hent_organisationer_for_borger(self, borger: dict, kun_aktive: bool = True) -> List[dict]:
        """
        Hent alle organisationer for en borger.

        :param borger: Borgeren der skal hentes organisationer for.
        :param kun_aktive: Om kun aktive organisationer skal returneres.
        :return: Alle organisations-relationer for borgeren. Disse relationer kan bruges til at redigere og slette forholdet.
        """
        response = self.nexus_client.get(
            borger["_links"]["patientOrganizations"]["href"]
        )

        if kun_aktive:
            return [org for org in response.json() if org["effectiveAtPresent"]]

        return response.json()

    def hent_borgere_for_organisation(self, organisation: dict) -> List[dict]:
        """
        Hent alle borgere for en organisation.

        :param organisation: Organisationen der skal hentes borgere for.
        :return: Alle borgere tilknyttet organisationen.
        """
        if "patients" not in organisation["_links"]:
            organisation = self.nexus_client.get(
                organisation["_links"]["self"]["href"]
            ).json()

        response = self.nexus_client.get(organisation["_links"]["patients"]["href"])
        return response.json()

    def hent_medarbejder_ved_initialer(self, initialer: str) -> dict:
        """
        Hent en medarbejder ved initialer.

        :param initialer: Initialerne på medarbejderen der skal hentes.
        :return: Medarbejderens detaljer.
        """
        url = self.nexus_client.api["professionals"]

        if url is None:
            raise ValueError("API indeholder ikke professionals endpoint.")
        
        response = self.nexus_client.get(url, params={"query": initialer})

        if response.status_code == 404:
            return None
                
        medarbejder = next((a for a in response.json() if a.get("primaryIdentifier") == initialer), None)
        return medarbejder

    def hent_medarbejdere_for_organisation(self, organisation: dict) -> List[dict]:
        """
        Hent alle medarbejdere for en organisation.

        :param organisation: Organisationen der skal hentes medarbejdere for.
        :return: Alle medarbejdere tilknyttet organisationen.
        """
        if "professionals" not in organisation["_links"]:
            organisation = self.nexus_client.get(
                organisation["_links"]["self"]["href"]
            ).json()

        response = self.nexus_client.get(
            organisation["_links"]["professionals"]["href"]
        )
        return response.json()

    def tilføj_borger_til_organisation(self, borger: dict, organisation: dict) -> bool:
        """
        Tilføj en borger til en organisation.

        :param borger: Borgeren der skal tilføjes til organisationen.
        :param organisation: Organisationen borgeren skal tilføjes til.
        :return: True hvis succesfuldt tilføjet, False ellers.
        """
        url = (
            borger["_links"]["patientOrganizations"]["href"] + f"/{organisation['id']}"
        )

        response = self.nexus_client.put(
            url,
            json="",
        )
        return response.status_code == 200

    def fjern_borger_fra_organisation(self, organisations_relation: dict) -> bool:
        """
        Fjern en borger fra en organisation.

        :param organisations_relation: Organisations-relationen der skal fjernes. Den kan hentes ved at kalde hent_organisationer_for_borger.
        :return: True hvis succesfuldt fjernet, False ellers.
        """
        if "removeFromPatient" not in organisations_relation["_links"]:
            organisations_relation = self.nexus_client.get(
                organisations_relation["_links"]["self"]["href"]
            ).json()
            
        response = self.nexus_client.delete(
            organisations_relation["_links"]["removeFromPatient"]["href"]
        )
        return response.status_code == 200

    def opdater_borger_organisations_relation(
        self,
        relation: dict,
        slut_dato: date,
        primær_organisation: bool,
    ) -> bool:
        """
        Opdater forholdet mellem en borger og en organisation.

        :param relation: Organisations-relationen der skal opdateres. Den kan hentes ved at kalde hent_organisationer_for_borger.
        :param slut_dato: Slutdatoen for forholdet. (kan være None)
        :param primær_organisation: Om organisationen er borgerens primære organisation.
        :return: True hvis succesfuldt opdateret, False ellers.
        """
        if slut_dato is not None:
            relation["effectiveEndDate"] = slut_dato.strftime("%Y-%m-%d")

        if primær_organisation is not None:
            relation["primaryOrganization"] = primær_organisation

        response = self.nexus_client.put(
            relation["_links"]["self"]["href"],
            json=relation,
        )
        return response.status_code == 200
    
    def opdater_leverandør(self, opdateret_leverandør: dict) -> dict:
        """
        Opdater en leverandør.

        :param opdateret_leverandør: Leverandøren der skal opdateres.
        :return: Den opdaterede leverandør.
        """
        try:
            response = self.nexus_client.put(
                opdateret_leverandør["_links"]["update"]["href"],
                json=opdateret_leverandør
            )
            return response.json()

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise