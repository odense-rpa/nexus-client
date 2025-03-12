from typing import List
from datetime import date

from kmd_nexus_client.client import NexusClient


class OrganizationsClient:
    def __init__(self, nexus_client: NexusClient):
        self.nexus_client = nexus_client

    def get_organizations(self) -> List[dict]:
        """
        Get all organizations.

        :return: All organizations.
        """
        response = self.nexus_client.get(self.nexus_client.api["organizations"])

        return response.json()
    
    def get_organization_by_name(self, name: str) -> dict:
        """
        Get organization by name.

        :param name: The name of the organization to retrieve.
        :return: The organization.
        """
        organizations = self.get_organizations()

        return [org for org in organizations if org["name"] == name][0]

    def get_organizations_by_citizen(self, citizen: dict, active_only=True):
        """
        Get all organizations by citizen.

        :param citizen: The citizen to retrieve organizations for.
        :return: All organizations relations by citizen. These relations can be used to edit and delete the relationship.
        """
        response = self.nexus_client.get(
            citizen["_links"]["patientOrganizations"]["href"]
        )

        if active_only:
            return [org for org in response.json() if org["effectiveAtPresent"]]

        return response.json()

    def get_citizens_by_organization(self, organization: dict):
        """
        Get all citizens by organization.

        :param organization: The organization to retrieve citizens for.
        """

        if "patients" not in organization["_links"]:
            organization = self.nexus_client.get(
                organization["_links"]["self"]["href"]
            ).json()

        response = self.nexus_client.get(organization["_links"]["patients"]["href"])

        return response.json()

    def get_professionals_by_organization(self, organization: dict):
        """
        Get all professionals by organization.

        :param organization: The organization to retrieve professionals for.
        """

        if "professionals" not in organization["_links"]:
            organization = self.nexus_client.get(
                organization["_links"]["self"]["href"]
            ).json()

        response = self.nexus_client.get(
            organization["_links"]["professionals"]["href"]
        )

        return response.json()

    def add_citizen_to_organization(self, citizen: dict, organization: dict) -> bool:
        """
        Add a citizen to an organization.

        :param citizen: The citizen to add to the organization.
        :param organization: The organization to add the citizen to.
        """
        # TODO: Figure out how to unit test this
        url = (
            citizen["_links"]["patientOrganizations"]["href"] + f"/{organization['id']}"
        )

        response = self.nexus_client.put(
            url,
            json="",
        )

        return response.status_code == 200

    def remove_citizen_from_organization(self, organization_relation: dict) -> bool:
        """
        Remove a citizen from an organization.

        :param organization_relation: The organization relation to remove. It can be acquired by calling get_organizations_by_citizen.
        """
        # TODO: Figure out how to unit test this
        if "removeFromPatient" not in organization_relation["_links"]:
            organization_relation = self.nexus_client.get(
                organization_relation["_links"]["self"]["href"]
            ).json()
            
        response = self.nexus_client.delete(
            organization_relation["_links"]["removeFromPatient"]["href"]
        )
        
        return response.status_code == 200

    def update_citizen_organization_relationship(
        self,
        organization_relation: dict,
        endDate: date,
        primary_organization: bool,
    ) -> bool:
        """
        Update the relationship between a citizen and an organization.

        :param citizen: The citizen to update the relationship for.
        :param organization_realtion: The organization to update the relationship for. It can be acquired by calling get_organizations_by_citizen.
        :param endDate: The end date of the relationship. (can be None)
        :param primary_contact: Whether the citizen is the primary contact for the organization.
        """
        # TODO: Figure out how to unit test this
        if endDate is not None:
            organization_relation["effectiveEndDate"] = endDate.strftime("%Y-%m-%d")

        if primary_organization is not None:
            organization_relation["primaryOrganization"] = primary_organization

        response = self.nexus_client.put(
            organization_relation["_links"]["update"]["href"],
            json=organization_relation,
        )

        return response.status_code == 200
