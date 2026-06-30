from typing import Optional
from httpx import HTTPStatusError
from datetime import date, datetime

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.models import PathwayEnsureResult
from kmd_nexus_client.utils import normalize_name


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
        except (HTTPStatusError, KeyError, TypeError):
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
                if names_match(base_case.get("name"), grundforløb_navn):
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
                            if names_match(x.get("name"), grundforløb_navn)
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

                # Genindlæs grundforløbsreference, til opretning af forløb.
                base_cases_response = self.client.get(
                    borger["_links"]["availablePathwayAssociation"]["href"]
                )

                if base_cases_response.status_code != 200:
                    return None

                base_cases = base_cases_response.json()

                # Find the matching base case
                matching_base_case = None
                for base_case in base_cases:
                    if names_match(base_case.get("name"), grundforløb_navn):
                        matching_base_case = base_case
                        break

                if not matching_base_case:
                    return None

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
                if names_match(program.get("name"), forløb_navn):
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
                if names_match(pathway.get("name"), forløb_navn):
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

    def sikr_forløb(
        self, borger: dict, grundforløb_navn: str, forløb_navn: str | None = None
    ) -> PathwayEnsureResult:
        """
        Ensure a citizen has the requested pathway/case.

        This treats existing active pathway associations as already satisfied,
        even when Nexus exposes the user-facing child name such as "Udlån" rather
        than the robot's conceptual parent label.

        :param borger: Borgeren der skal have forløbet.
        :param grundforløb_navn: Grundforløbets navn.
        :param forløb_navn: Valgfrit underforløb/sag.
        :return: Resultat med om noget blev oprettet.
        :raises RuntimeError: Hvis forløbet ikke kan sikres.
        """
        existing = self._find_existing_pathway_association(
            borger, grundforløb_navn, forløb_navn
        )
        if existing is not None:
            return PathwayEnsureResult(
                created=False,
                base_case=existing if forløb_navn is None else None,
                case=existing if forløb_navn is not None else None,
            )

        result = self.opret_forløb(borger, grundforløb_navn, forløb_navn)
        if result is None:
            raise RuntimeError(
                f"Could not ensure Nexus forløb: {grundforløb_navn}"
                + (f" > {forløb_navn}" if forløb_navn else "")
            )

        return PathwayEnsureResult(
            created=True,
            base_case=result.get("base_case"),
            case=result.get("case"),
        )

    def find_forløb_association(
        self, borger: dict, grundforløb_navn: str, forløb_navn: str | None = None
    ) -> dict | None:
        """Find an active pathway association by normalized root or child label."""
        return self._find_existing_pathway_association(
            borger, grundforløb_navn, forløb_navn
        )

    def _find_existing_pathway_association(
        self, borger: dict, grundforløb_navn: str, forløb_navn: str | None
    ) -> dict | None:
        """Find an existing pathway association matching root or child label."""
        try:
            response = self.client.get(
                borger["_links"]["availablePathwayAssociation"]["href"]
            )
        except HTTPStatusError:
            return None

        if response.status_code != 200:
            return None

        associations = response.json()
        if not isinstance(associations, list):
            return None

        names = [forløb_navn] if forløb_navn else [grundforløb_navn]
        return next(
            (
                association
                for association in associations
                if association.get("pathwayStatus") in (None, "ACTIVE")
                and any(names_match(association.get("name"), name) for name in names)
            ),
            None,
        )

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
            unclosable_link = case_details.get("_links", {}).get(
                "unclosableReferences", {}
            )
            if unclosable_link.get("href"):
                unclosable_response = self.client.get(unclosable_link["href"])

                if unclosable_response.status_code != 200:
                    return False

                unclosable_data = unclosable_response.json()

                # If there are unclosable references, cannot close
                if len(unclosable_data) > 0:
                    return False

            close_link = case_details.get("_links", {}).get("close", {}).get("href")
            if not close_link:
                patient_pathway_link = (
                    case_details.get("_links", {}).get("patientPathway", {}).get("href")
                )
                if patient_pathway_link:
                    patient_pathway_response = self.client.get(patient_pathway_link)
                    if patient_pathway_response.status_code != 200:
                        return False
                    return self._inactivate_forløb(patient_pathway_response.json())
                return self._inactivate_forløb(case_details)

            # Close the case
            close_response = self.client.put(close_link, json={})

            return close_response.status_code == 200

        except HTTPStatusError:
            return False

    def _inactivate_forløb(self, forløb: dict) -> bool:
        """Fallback close for Nexus patient pathways that expose update only."""
        update_link = forløb.get("_links", {}).get("update", {}).get("href")
        if not update_link:
            return False
        payload = dict(forløb)
        payload["active"] = False
        payload["inactivatedDate"] = date.today().isoformat()
        response = self.client.put(update_link, json=payload)
        return response.status_code == 200

    def opret_dokument(
        self,
        borger: dict,
        forløb: dict,
        fil: bytes,
        filnavn: str,
        titel: str,
        noter: Optional[str],
        modtaget: datetime,
        indholdstype: str = "application/pdf",
    ) -> dict | None:
        """
        Opret et dokument for en borger i et forløb.

        :param borger: Borgerens oplysninger.
        :param forløb: Forløbets oplysninger.
        :param fil: Filen der skal uploades.
        :param filnavn: Navnet på filen.
        :param titel: Titlen på dokumentet.
        :param noter: Noter til dokumentet.
        :param modtaget: Dato og tid for modtagelse.
        :param indholdstype: Indholdstypen for dokumentet (default: "application/pdf").
        :return: True hvis dokumentet blev oprettet, False ellers.
        """
        try:
            prototype = self.client.get(forløb["_links"]["documentPrototype"]["href"])

            if prototype.status_code != 200:
                return None

            dokument = prototype.json()
            dokument["name"] = titel
            dokument["notes"] = noter
            dokument["relevanceDate"] = modtaget.isoformat()  # to UTC string
            dokument["originalFileName"] = filnavn

            oprettet_dokument = self.client.post(
                dokument["_links"]["create"]["href"], json=dokument
            )

            if oprettet_dokument.status_code != 200:
                return None

            # Upload the file using self.client, which handles authentication
            upload_url = (
                oprettet_dokument.json().get("_links", {}).get("upload", {}).get("href")
            )

            if not upload_url:
                return None

            files = {"file": (filnavn, fil, indholdstype)}
            resp = self.client.post(upload_url, files=files, json={})

            if resp.status_code != 200:
                return None
            return resp.json()

        except HTTPStatusError:
            return None


def names_match(actual: str | None, expected: str | None) -> bool:
    """Return whether two Nexus pathway labels match after normalization."""
    return normalize_name(actual) == normalize_name(expected)
