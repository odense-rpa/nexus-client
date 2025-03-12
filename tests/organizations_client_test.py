import pytest

from .fixtures import organizations_client, base_client, test_citizen, citizens_client # noqa
from kmd_nexus_client.functionality.organizations import OrganizationsClient

def test_get_organizations(organizations_client: OrganizationsClient):
    organizations = organizations_client.get_organizations()

    assert organizations is not None
    assert len(organizations) > 0

def test_get_organization_by_name(organizations_client: OrganizationsClient):
    organization = organizations_client.get_organization_by_name("Sundhedsfagligt Team")

    assert organization is not None
    assert organization["name"] == "Sundhedsfagligt Team"

def test_get_organizations_by_citizen(
    organizations_client: OrganizationsClient, test_citizen: dict
):
    organizations = organizations_client.get_organizations_by_citizen(
        test_citizen, active_only=False
    )

    assert organizations is not None
    assert len(organizations) > 0

    active_organizations = organizations_client.get_organizations_by_citizen(
        test_citizen, active_only=True
    )

    assert active_organizations is not None
    assert len(active_organizations) > 0
    assert len(active_organizations) < len(organizations)
    
    
def test_get_citizens_by_organization(organizations_client: OrganizationsClient):
    organizations = organizations_client.get_organizations()    
    organization = [x for x in organizations if x["name"] == "Sundhedsfagligt Team"][0]
    citizens = organizations_client.get_citizens_by_organization(organization)
    
    assert citizens is not None
    assert len(citizens) > 0
    
def test_get_professionals_by_organization(organizations_client: OrganizationsClient):
    organizations = organizations_client.get_organizations()    
    organization = [x for x in organizations if x["name"] == "Sundhedsfagligt Team"][0]        
    professionals = organizations_client.get_professionals_by_organization(organization)
    
    assert professionals is not None
    assert len(professionals) > 0