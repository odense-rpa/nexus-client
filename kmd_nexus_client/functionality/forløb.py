from typing import Optional
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient


class ForløbClient:
    """
    Klient til forløbs-operationer i KMD Nexus.
    
    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.forløb.hent_forløb(...)
    """
    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def hent_forløb(self, borger: dict) -> Optional[dict]:
        """
        Hent aktive forløb for en borger.

        :param borger: Borgeren der skal hentes forløb for.
        :return: Borgerens aktive forløb, eller None hvis hentning fejlede.
        """
        # TODO: Output er ikke tilsvarende pathway_references og fungerer derfor ikke med luk_forløb. Bør streamlines.
        try:
            response = self.client.get(borger["_links"]["activePrograms"]["href"])
            return response.json()
        except HTTPStatusError:
            return None

    def opret_forløb(
        self, borger: dict, grundforløb_navn: str, forløb_navn: str = None
    ) -> Optional[dict]:
        """
        Opret et nyt forløb for en borger.

        :param borger: Borgeren der skal oprettes forløb for.
        :param grundforløb_navn: Navnet på grundforløbet f.eks. "Sundhedsfagligt grundforløb".
        :param forløb_navn: Navnet på det specifikke forløb. Hvis None, oprettes kun grundforløb.
        :return: Dictionary med 'base_case' og 'case' (hvis oprettet), eller None hvis oprettelse fejlede.
        """
        try:
            # Get available pathway associations (grundforløb)
            base_cases_response = self.client.get(
                borger["_links"]["availablePathwayAssociation"]["href"]
            )

            if base_cases_response.status_code != 200:
                return None

            base_cases = base_cases_response.json()

            # Find the matching base case
            matching_base_case = None
            for base_case in base_cases:
                if base_case.get("name") == grundforløb_navn:
                    matching_base_case = base_case
                    break

            # Enroll in the base case
            if not matching_base_case:
                available_cases = self.client.get(
                    borger["_links"]["availableProgramPathways"]["href"]
                )
                matching_base_case = next(
                    iter(
                        [
                            x
                            for x in list(available_cases.json())
                            if x["name"] == grundforløb_navn
                        ]
                    ),
                    None,
                )

                if not matching_base_case:
                    return None

                enroll_response = self.client.put(
                    matching_base_case["_links"]["enroll"]["href"], json={}
                )

                if enroll_response.status_code != 200:
                    return None

                matching_base_case = enroll_response.json()

            # If no specific case name provided, return just the base case
            if not forløb_navn:
                return {"base_case": matching_base_case, "case": None}

            # Get available pathways for the base case
            pathways_response = self.client.get(
                matching_base_case["_links"]["self"]["href"]
            )

            if pathways_response.status_code != 200:
                return None

            base_case_details = pathways_response.json()

            # Get active programs to check if case already exists
            active_programs_response = self.client.get(
                base_case_details["_links"]["activePrograms"]["href"]
            )

            # Check if case already exists in active programs
            active_programs = (
                active_programs_response.json()
                if active_programs_response.status_code == 200
                else []
            )

            existing_case = None
            for program in active_programs:
                if program.get("name") == forløb_navn:
                    existing_case = program
                    break

            if existing_case:
                return {"base_case": base_case_details, "case": existing_case}

            # Get available nested program pathways
            available_pathways_response = self.client.get(
                base_case_details["_links"]["availableNestedProgramPathways"]["href"]
            )

            if available_pathways_response.status_code != 200:
                return None

            available_pathways = available_pathways_response.json()

            # Find the matching pathway
            matching_pathway = None
            for pathway in available_pathways:
                if pathway.get("name") == forløb_navn:
                    matching_pathway = pathway
                    break

            if not matching_pathway:
                return None

            # Create the case by enrolling in the pathway
            enroll_response = self.client.put(
                matching_pathway["_links"]["enroll"]["href"], json={}
            )

            if enroll_response.status_code == 200:
                created_case = enroll_response.json()
                return {"base_case": base_case_details, "case": created_case}

            return None

        except HTTPStatusError:
            return None

    def luk_forløb(self, forløb_reference: dict) -> bool:
        """
        Luk et forløb hvis muligt.

        :param forløb_reference: Forløb referencen der skal lukkes.
        :return: True hvis succesfuldt lukket, False ellers.
        """
        try:
            # Get full case details
            case_details_response = self.client.get(
                forløb_reference["_links"]["self"]["href"]
            )

            if case_details_response.status_code != 200:
                return False

            case_details = case_details_response.json()

            # Check for unclosable references
            unclosable_response = self.client.get(
                case_details["_links"]["unclosableReferences"]["href"]
            )

            if unclosable_response.status_code != 200:
                return False

            unclosable_data = unclosable_response.json()

            # If there are unclosable references, cannot close
            if len(unclosable_data) > 0:
                return False

            # Close the case
            close_response = self.client.put(
                case_details["_links"]["close"]["href"], json={}
            )

            return close_response.status_code == 200

        except HTTPStatusError:
            return False
    
