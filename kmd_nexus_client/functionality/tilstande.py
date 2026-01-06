from datetime import date
from typing import List

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.utils import sanitize_cpr


class TilstandeClient:
    """
    Klient til tilstands-operationer i KMD Nexus.

    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.tilstande.hent_tilstande(...)
    """

    def __init__(self, nexus_client: NexusClient):
        self.nexus_client = nexus_client

    def hent_tilstande(self, borger: dict) -> List[dict]:
        """
        Hent tilstande for en given borger baseret på CPR-nummer.
        :param cpr: CPR-nummer for borgeren.
        :return: Liste af tilstande.
        """
        response = self.nexus_client.get(borger["_links"]["patientConditions"]["href"])

        return response.json()

    def hent_tilstandstyper(self, borger: dict) -> List[dict]:
        """
        Hent tilstandstyper for en given borger baseret på CPR-nummer. Disse kan anvendes ved oprettelse af nye tilstande.
        :param cpr: CPR-nummer for borgeren.
        :return: Liste af tilstandstyper.
        """
        response = self.nexus_client.get(
            borger["_links"]["availableConditionClassifications"]["href"]
        )

        return response.json()

    def opret_tilstand(self, borger: dict, tilstandstype: dict) -> dict:
        """
        Opret en ny tilstand for en given borger.
        :param borger: Borgerens data.
        :param tilstandstype: Tilstandstype data til oprettelse.
        :return: Oprettet tilstands data.
        """
        # conditionPrototype
        # newObservationsPrototype

        prototype_url = (
            tilstandstype["_links"]
            .get(
                "conditionPrototype",
                tilstandstype["_links"].get("newObservationsPrototype"),
            )
            .get("href")
        )

        prototype = self.nexus_client.get(prototype_url).json()

        state_value = [
            s for s in prototype["state"]["possibleValues"] if s["code"] == "PCActive"
        ][0]

        prototype["state"]["value"] = state_value

        response = self.nexus_client.post(
            prototype["_links"]["create"]["href"], json=prototype
         )

        # Der returneres en liste fordi man teknisk kan multi-oprette tilstande, det gør vi bare ikke
        return response.json()[0]


    def rediger_tilstand(self, tilstand: dict, status: str = "PCActive", **kwargs) -> dict:
        """
        Rediger en eksisterende tilstand for en given borger.
        :param tilstand: Tilstands data.
        :param status: Ny status kode for tilstanden.
        :param kwargs: Yderligere felter der skal opdateres.
        :return: Opdateret tilstands data.
        """

        prototype = self.nexus_client.get(
            tilstand["_links"]["observationsPrototype"]["href"]
        ).json()

        # Opdater status
        state_value = [
            s for s in prototype["state"]["possibleValues"] if s["code"] == status
        ][0]

        prototype["state"]["value"] = state_value

        # Opdater yderligere felter
        for key, value in kwargs.items():

            if key not in prototype:
                raise ValueError(f"Feltet '{key}' findes ikke i tilstanden.")
            
            if prototype[key]["type"] == "singleValue":
                matched_value = next(
                         (v for v in prototype[key]["possibleValues"] if (v["code"] == value or v["name"] == value)), None
                     )
                
                if matched_value:
                    prototype[key]["value"] = matched_value
                else:
                    raise ValueError(
                        f"Ugyldig værdi '{value}' for feltet '{key}'."
                    )
                continue

            if prototype[key]["type"] == "string":
                prototype[key]["value"] = value
                continue

        response = self.nexus_client.post(
            prototype["_links"]["create"]["href"], json=prototype
         )

        conditions = response.json()
        return conditions[0]  # Returner den opdaterede tilstand
