from typing import Optional, List
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient


class CasesClient:
    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def get_citizen_cases(self, citizen: dict) -> Optional[dict]:
        """
        Get active cases (forløb) for a citizen.

        :param citizen: The citizen to retrieve cases for.
        :return: The citizen's active cases, or None if retrieval failed.
        """
        try:
            response = self.client.get(citizen["_links"]["activePrograms"]["href"])
            return response.json()
        except HTTPStatusError:
            return None

    def create_citizen_case(
        self, citizen: dict, base_case_name: str, case_name: str = None
    ) -> Optional[dict]:
        """
        Create a new case (forløb) for a citizen.

        :param citizen: The citizen to create a case for.
        :param base_case_name: The name of the base case (grundforløb) e.g., "Sundhedsfagligt grundforløb".
        :param case_name: The name of the specific case (forløb). If None, only base case is created.
        :return: Dictionary with 'base_case' and 'case' (if created), or None if creation failed.
        """
        try:
            # Get available pathway associations (grundforløb)
            base_cases_response = self.client.get(
                citizen["_links"]["availablePathwayAssociation"]["href"]
            )

            if base_cases_response.status_code != 200:
                return None

            base_cases = base_cases_response.json()

            # Find the matching base case
            matching_base_case = None
            for base_case in base_cases:
                if base_case.get("name") == base_case_name:
                    matching_base_case = base_case
                    break

            # Enroll in the base case
            if not matching_base_case:
                available_cases = self.client.get(
                    citizen["_links"]["availableProgramPathways"]["href"]
                )
                matching_base_case = next(
                    iter(
                        [
                            x
                            for x in list(available_cases.json())
                            if x["name"] == base_case_name
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
            if not case_name:
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
                if program.get("name") == case_name:
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
                if pathway.get("name") == case_name:
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

    def close_case(self, case_reference: dict) -> bool:
        """
        Close a case (forløb) if possible.

        :param case_reference: The case reference to close.
        :return: True if successfully closed, False otherwise.
        """
        try:
            # Get full case details
            case_details_response = self.client.get(
                case_reference["_links"]["self"]["href"]
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
