from collections.abc import Mapping
from typing import Any, Optional, List
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.models import NexusBorger
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
        return self._hent_borger_payload(cpr)

    def find_borger_by_cpr(self, borger_cpr: str) -> NexusBorger | None:
        """
        Find a citizen by CPR and return the stable fields robot workflows need.

        The primary Nexus details lookup sometimes responds with 404 even when
        the citizen can be found through the broader search endpoint. This method
        keeps that API-specific fallback and response-shape handling inside the
        client instead of every robot workflow.
        """
        cpr = sanitize_cpr(borger_cpr)
        payload: Mapping[str, Any] | None = self._hent_borger_payload(cpr)

        if payload is None:
            payload = self._find_borger_payload_by_search(cpr)

        if payload is None:
            return None

        return parse_nexus_borger(payload, fallback_cpr=cpr)

    def _hent_borger_payload(self, cpr: str) -> Optional[dict]:
        """Return the raw Nexus patient payload from the details endpoint."""

        try:
            response = self.client.post(
                self.client.api["patientDetailsSearch"],
                json={"businessKey": cpr, "keyType": "CPR"},
            )

            data = response.json()

            if data.get("isPatientAccessible") is False:
                return None

            patient = data.get("patient")
            if not isinstance(patient, dict):
                return None
            return patient

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def _find_borger_payload_by_search(self, cpr: str) -> Mapping[str, Any] | None:
        """Return an exact CPR match from Nexus' broader patient search."""
        for result in self.søg_borgere(cpr, antal=10):
            if not isinstance(result, Mapping):
                continue
            if parse_nexus_patient_identifier(result) == cpr:
                return result
        return None

    def søg_borgere(self, søgning: str, antal: int = 10) -> List[dict]:
        """
        Søg efter borgere baseret på en søgestreng.

        :param søgning: Søgestrengen der skal bruges til at finde borgere (f.eks. navn eller del af CPR).
        :param antal: Antal resultater der skal returneres (standard: 10).
        :return: En liste af borgere der matcher søgningen.
        """

        response = self.client.get(
            self.client.api["searchPatients"],
            params={"query": søgning, "maxResults": antal},
        )

        return response.json()

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

    def hent_udlån(self, borger: dict) -> List[dict] | None:
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

    def opret_borger(self, borger_cpr: str) -> dict | None:
        """
        Opret en ny borger i KMD Nexus.

        :param borger_data: Data for den nye borger.
        :param cpr: CPR nummeret på borgeren der skal oprettes.
        :return: Det oprettede borgerobjekt.
        """

        cpr = sanitize_cpr(borger_cpr)

        try:
            prototype_response = self.client.get(
                f"{self.client.api['patients']}/prototypeBasedOnCprSystem?cpr={cpr}"
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

    def opret_netværksperson(self, borger, netværksperson_data: dict) -> dict:
        """
        Opret en netværksperson for en borger.

        :param borger: Borgeren der skal oprettes en netværksperson for.
        :param netværksperson_data: Data for den nye netværksperson.
        :return: Det oprettede netværksperson objekt.
        """

        netværksperson_prototype = self.client.get(
            borger["_links"]["patientNetworkContactPrototype"]["href"]
        ).json()

        for key, value in netværksperson_data.items():
            netværksperson_prototype[key] = value

        response = self.client.post(
            netværksperson_prototype["_links"]["create"]["href"],
            json=netværksperson_prototype,
        )

        return response.json()


def parse_nexus_borger(
    payload: Mapping[str, Any], fallback_cpr: str | None = None
) -> NexusBorger | None:
    """Parse the stable citizen fields from known Nexus patient payload shapes."""
    cpr = parse_nexus_patient_identifier(payload)
    if cpr is None and fallback_cpr is not None:
        cpr = normalize_cpr_digits(fallback_cpr)
    if cpr is None:
        return None

    raw_id = payload.get("id")
    return NexusBorger(
        citizen_id=str(raw_id) if raw_id is not None else None,
        display_name=parse_nexus_citizen_name(payload),
        cpr=cpr,
    )


def parse_nexus_citizen_name(payload: Mapping[str, Any]) -> str | None:
    """Extract a readable citizen name from Nexus payload data."""
    for field in ("fullName", "displayName", "name"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value

    first_name = payload.get("firstName")
    last_name = payload.get("lastName")
    name_parts = [
        value.strip()
        for value in (first_name, last_name)
        if isinstance(value, str) and value.strip()
    ]
    return " ".join(name_parts) if name_parts else None


def parse_nexus_patient_identifier(payload: Mapping[str, Any]) -> str | None:
    """Extract normalized CPR digits from known Nexus patient identifier shapes."""
    match payload:
        case {"patientIdentifier": str(identifier)}:
            return normalize_cpr_digits(identifier)
        case {"patientIdentifier": {"identifier": str(identifier)}}:
            return normalize_cpr_digits(identifier)
        case _:
            return None


def normalize_cpr_digits(value: str) -> str | None:
    """Return CPR digits from a Nexus identifier when it has the expected shape."""
    digits = "".join(char for char in value if char.isdigit())
    if len(digits) != 10:
        return None
    return digits
