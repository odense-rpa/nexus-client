from datetime import date
from typing import Iterable, List
from urllib.parse import urlencode

from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.models import OrganisationRelationEnsureResult
from kmd_nexus_client.utils import normalize_name
from kmd_nexus_client.utils import sanitize_citizen_identifier


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

    def __init__(
        self,
        nexus_client: NexusClient,
        hcl_depot_order_filter_configuration_ids: Iterable[str] | None = None,
    ):
        self.nexus_client = nexus_client
        self.hcl_depot_order_filter_configuration_ids = tuple(
            filter_id.strip()
            for filter_id in (hcl_depot_order_filter_configuration_ids or ())
            if filter_id.strip()
        )

    def hent_organisationer(self) -> List[dict]:
        """
        Hent alle organisationer.

        :return: Alle organisationer.
        """
        response = self.nexus_client.get(self.nexus_client.api["organizations"])
        return response.json()

    def hent_organisationer_med_træhierarki(self) -> List[dict]:
        """
        Hent alle organisationer med deres træhierarki.

        :return: Alle organisationer med træhierarki.
        """

        response = self.nexus_client.get(self.nexus_client.api["organizationsTree"])
        return response.json()

    def hent_leverandører(self) -> List[dict]:
        """
        Hent alle leverandører.

        :return: Alle leverandører.
        """
        response = self.nexus_client.get(self.nexus_client.api["suppliers"])
        return response.json()

    def hent_organisation_ved_navn(self, navn: str) -> dict | None:
        """
        Hent organisation ved navn.

        :param navn: Navnet på organisationen der skal hentes.
        :return: Organisationen.
        """
        organisationer = self.hent_organisationer()
        expected = normalize_name(navn)
        return next(
            (
                org
                for org in organisationer
                if normalize_name(org.get("name")) == expected
            ),
            None,
        )

    def sikr_borger_i_organisation(
        self, borger: dict, organisation_navn: str
    ) -> OrganisationRelationEnsureResult:
        """
        Ensure a citizen has an active relation to an organisation.

        :param borger: Borgeren der skal have organisationsrelationen.
        :param organisation_navn: Organisationens navn. Sammenlignes normaliseret.
        :return: Resultat med relationen og om den blev oprettet.
        :raises ValueError: Hvis organisationen ikke findes i Nexus.
        :raises RuntimeError: Hvis relationen ikke kan oprettes eller genfindes.
        """
        existing_relations = self.hent_organisationer_for_borger(borger)
        existing_relation = find_organisation_relation(
            existing_relations, organisation_navn
        )
        organisation = self.hent_organisation_ved_navn(organisation_navn)

        if existing_relation is not None:
            if organisation is None:
                organisation = existing_relation.get("organization", {})
            return OrganisationRelationEnsureResult(
                created=False,
                relation=existing_relation,
                organisation=organisation,
            )

        if organisation is None:
            raise ValueError(f"Nexus organisation not found: {organisation_navn}")

        if not self.tilføj_borger_til_organisation(borger, organisation):
            raise RuntimeError(
                f"Could not attach borger to Nexus organisation: {organisation_navn}"
            )

        updated_relations = self.hent_organisationer_for_borger(borger)
        relation = find_organisation_relation(updated_relations, organisation_navn)
        if relation is None:
            raise RuntimeError(
                f"Could not find created Nexus organisation relation: {organisation_navn}"
            )

        return OrganisationRelationEnsureResult(
            created=True,
            relation=relation,
            organisation=organisation,
        )

    def hent_organisationer_for_borger(
        self, borger: dict, kun_aktive: bool = True
    ) -> List[dict]:
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

    def hent_medarbejder_ved_initialer(self, initialer: str) -> dict | None:
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

        medarbejder = next(
            (a for a in response.json() if a.get("primaryIdentifier") == initialer),
            None,
        )
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

    def fjern_medarbejder_fra_forløb(self, medarbejder_reference: dict) -> bool:
        """
        Fjern en medarbejder fra et forløb.

        :param forløb: Forløbet der skal fjernes medarbejderen fra.
        :param medarbejder: Medarbejderen der skal fjernes fra forløbet.
        :return: True hvis succesfuldt fjernet, False ellers.
        """

        medarbejder = self.nexus_client.hent_fra_reference(medarbejder_reference)

        response = self.nexus_client.delete(medarbejder["_links"]["delete"]["href"])

        return response.status_code == 200

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
        links = organisations_relation.get("_links") or {}
        if "removeFromPatient" not in links and "self" in links:
            organisations_relation = self.nexus_client.get(
                links["self"]["href"]
            ).json()
            links = organisations_relation.get("_links") or {}

        remove_link = links.get("removeFromPatient")
        if isinstance(remove_link, dict) and remove_link.get("href"):
            response = self.nexus_client.delete(remove_link["href"])
            return response.status_code == 200

        return False

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
                json=opdateret_leverandør,
            )
            return response.json()

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def hent_borgere_med_udlåns_bestillinger(self) -> List[str] | None:
        """
        Hent alle borgere med udlånsbestillinger.

        :return: Liste over borgere med udlånsbestillinger, eller None hvis ingen findes.
        """
        borgere = []

        for filter_id in self.hcl_depot_order_filter_configuration_ids:
            ordrer = self.nexus_client.get(hcl_depot_orders_endpoint(filter_id)).json()
            for ordre in ordrer:
                try:
                    cpr = sanitize_citizen_identifier(
                        ordre["receiver"]["patientIdentifier"]
                    )

                    if cpr not in borgere:
                        borgere.append(cpr)
                except ValueError:
                    continue

        return borgere if borgere else None


def hcl_depot_orders_endpoint(order_filter_configuration_id: str) -> str:
    """Build an instance-relative HCL depot orders endpoint."""
    query = urlencode({"orderFilterConfigurationId": order_filter_configuration_id})
    return f"/api/hcl-depot/orders?{query}"


def find_organisation_relation(
    relations: List[dict], organisation_navn: str
) -> dict | None:
    """Find a citizen organisation relation by normalized organisation name."""
    expected = normalize_name(organisation_navn)
    return next(
        (
            relation
            for relation in relations
            if normalize_name(relation.get("organization", {}).get("name")) == expected
        ),
        None,
    )
