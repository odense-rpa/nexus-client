from datetime import date
from httpx import HTTPStatusError
from kmd_nexus_client.client import NexusClient
from typing import List, Optional


class OpgaverClient:
    """
    Klient til håndtering af opgaver i KMD Nexus.

    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.opgaver.hent_opgave(...)

    Danske funktioner:
    - hent_opgaver(objekt) -> List[dict]
    - hent_opgave_for_borger(borger, opgave_id) -> Optional[dict]
    - hent_opgavetyper(objekt) -> List[dict]
    - opret_opgave(objekt, opgave_type, titel, ansvarlig_organisation, start_dato,
                   forfald_dato=None, beskrivelse=None, ansvarlig_medarbejder=None) -> dict
    - rediger_opgave(opdateret_opgave) -> dict
    - luk_opgave(opgave) -> bool

    Backward compatibility (DEPRECATED):
    - get_assignments, get_assignment_by_citizen, create_assignment,
      edit_assignment, close_assignment
    """

    def __init__(self, nexus_client: NexusClient):
        self.nexus_client = nexus_client

    def hent_opgaver(self, objekt: dict) -> List[dict]:
        """
        Hent alle opgaver for et objekt.

        :param objekt: Objektet der skal hentes opgaver for.
        :return: Alle opgaver for objektet.
        """
        # Validate if object contains availableAssignmentTypes:
        if "availableAssignmentTypes" not in objekt["_links"]:
            raise ValueError("Objekt indeholder ikke availableAssignmentTypes link.")

        response = self.nexus_client.get(objekt["_links"]["activeAssignments"]["href"])

        return response.json()

    def hent_opgave_for_borger(self, borger: dict, opgave_id: int) -> Optional[dict]:
        # The way the API is called in this function is an exception, by directly using a hardcoded path, instead of using the HATEOAS design.
        # The alternative is to map assignment ids from the database to the citizen activity and reference json.
        """
        Hent en specifik opgave for en borger via ID.

        :param borger: Borgeren der skal hentes opgave for.
        :param opgave_id: ID'et på opgaven der skal hentes.
        :return: Opgave detaljer, eller None hvis ikke fundet.
        """
        if not isinstance(borger, dict):
            return None

        response = self.nexus_client.get(
            f"assignments/patient/{borger['id']}/assignments?ids={opgave_id}"
        )

        if response.status_code == 404:
            return None

        return response.json()[0] if response.json() else None

    def hent_opgavetyper(self, objekt: dict) -> List[dict]:
        """
        Hent tilgængelige opgavetyper for et objekt.

        :param objekt: Objektet der skal hentes opgavetyper for.
        :return: Liste af tilgængelige opgavetyper.
        """
        # Validate if object contains availableAssignmentTypes:
        if "availableAssignmentTypes" not in objekt.get("_links", {}):
            raise ValueError("Objekt indeholder ikke availableAssignmentTypes link.")

        response = self.nexus_client.get(
            objekt["_links"]["availableAssignmentTypes"]["href"]
        )
        return response.json()

    def opret_opgave(
        self,
        objekt: dict,
        opgave_type: str,
        titel: str,
        ansvarlig_organisation: str,
        start_dato: date,
        forfald_dato: Optional[date] = None,
        beskrivelse: Optional[str] = None,
        ansvarlig_medarbejder: Optional[dict] = None,
    ) -> dict:
        """
        Opret en ny opgave.

        :param objekt: Objektet der skal oprettes opgave for.
        :param opgave_type: Typen af opgaven.
        :param titel: Titlen på opgaven.
        :param ansvarlig_organisation: Organisationen der er ansvarlig for opgaven.
        :param ansvarlig_medarbejder: Medarbejderen der er ansvarlig for opgaven.
        :param beskrivelse: Beskrivelsen af opgaven.
        :param start_dato: Startdatoen for opgaven.
        :param forfald_dato: Forfaldsdatoen for opgaven. Kan være None hvis ikke specificeret.
        :return: Den oprettede opgave.
        """

        # Get available assignment types using the new method
        available_assignment_types = self.hent_opgavetyper(objekt)

        # Find the correct assignment type
        found_assignment_type = next(
            (
                item
                for item in available_assignment_types
                if item["name"] == opgave_type
            ),
            None,
        )

        if not found_assignment_type:
            raise ValueError(
                f"Opgave type {opgave_type} ikke fundet i tilgængelige opgave typer."
            )

        # Get prototype
        prototype = self.nexus_client.get(
            found_assignment_type["_links"]["assignmentPrototype"]["href"]
        ).json()

        # Find correct organization
        possible_organizations = self.nexus_client.get(
            prototype["_links"]["availableOrganizationAssignees"]["href"]
        ).json()
        probable_organization = next(
            (
                item
                for item in possible_organizations
                if item["name"] == ansvarlig_organisation
            ),
            None,
        )
        if not probable_organization:
            raise ValueError(
                f"Organisation {ansvarlig_organisation} ikke fundet i tilgængelige organisationer."
            )

        # Skip responsible worker for now - need more help

        # Find the correct action type
        action_type = next(
            (
                action
                for action in prototype["actions"]
                if action.get("name") == "Opret"
            ),
            None,
        )
        if not action_type:
            raise ValueError("Action type 'Opret' ikke fundet i prototype actions.")

        # Edit prototype with values
        prototype["object"] = objekt
        prototype["title"] = titel
        # prototype["assignmentType"] = assignment_type
        prototype["organizationAssignee"] = {
            "organizationId": int(probable_organization["id"]),
            "displayName": str(probable_organization["name"]),
        }
        prototype["startDate"] = start_dato.strftime("%Y-%m-%d")
        if forfald_dato:
            prototype["dueDate"] = forfald_dato.strftime("%Y-%m-%d")
        if beskrivelse:
            prototype["description"] = beskrivelse
        if ansvarlig_medarbejder:
            # ask MIWN how to get responsible worker
            prototype["professionalAssignee"] = {
                "professionalId": int(ansvarlig_medarbejder["id"]),
                "displayName": str(ansvarlig_medarbejder["fullName"]),
                "displayNameWithUniqId": f"{ansvarlig_medarbejder['fullName']} ({ansvarlig_medarbejder['primaryIdentifier']})",
                "active": bool(ansvarlig_medarbejder["active"]),
            }

        # Create assignment
        response = self.nexus_client.post(
            action_type["_links"]["createAssignment"]["href"],
            json=prototype,
        )

        return response.json()

    def rediger_opgave(self, opdateret_opgave: dict) -> dict:
        """
        Rediger en eksisterende opgave.

        :param opdateret_opgave: Den opdaterede opgave.
        :return: Den redigerede opgave.
        """
        try:
            handling = next(
                (a for a in opdateret_opgave["actions"] if a.get("name") == "Gem"), None
            )

            if not handling:
                raise ValueError("Ingen 'Gem' action fundet i opgave actions.")

            response = self.nexus_client.put(
                handling["_links"]["updateAssignment"]["href"], json=opdateret_opgave
            )

            return response.json()

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def luk_opgave(self, opgave: dict) -> bool:
        """
        Luk en opgave hvis muligt.

        :param opgave: Opgaven der skal lukkes.
        :return: True hvis succesfuldt lukket, False ellers.
        """
        try:
            # Check if the assignment has actions available
            if "actions" not in opgave:
                return False

            actions = opgave["actions"]

            # Find the "Afslut" action in the list
            afslut_action = None
            for action in actions:
                if isinstance(action, dict) and action.get("name") == "Afslut":
                    afslut_action = action
                    break

            if not afslut_action:
                return False

            # Execute the close action
            response = self.nexus_client.put(
                afslut_action["_links"]["updateAssignment"]["href"], json=opgave
            )

            # Accept both 200 OK and 204 No Content as success
            return response.status_code in [200, 204]

        except HTTPStatusError:
            return False
