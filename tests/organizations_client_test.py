import pytest

from .fixtures import organizations_client, base_client, test_citizen, citizens_client # noqa
from kmd_nexus_client.functionality.organizations import OrganizationsClient
from kmd_nexus_client.functionality.citizens import (CitizensClient)

def test_get_organizations(organizations_client: OrganizationsClient):
    organizations = organizations_client.get_organizations()

    assert organizations is not None
    assert len(organizations) > 0

def test_get_suppliers(organizations_client: OrganizationsClient):
    suppliers = organizations_client.get_suppliers()

    assert suppliers is not None
    assert len(suppliers) > 0
    assert all("name" in supplier for supplier in suppliers)
    assert all("id" in supplier for supplier in suppliers)

def test_update_supplier(organizations_client: OrganizationsClient, citizens_client: CitizensClient):
    suppliers = organizations_client.get_suppliers()
    supplier = [x for x in suppliers if x["name"] == "Testleverandør Supporten Træning"][0]
    assert supplier is not None
    
    resolved_supplier = citizens_client.resolve_reference(supplier)
    resolved_supplier["address"]["administrativeAreaCode"] = "461"

    updated_supplier = organizations_client.update_supplier(resolved_supplier)    
    assert updated_supplier is not None
    assert updated_supplier["address"]["administrativeAreaCode"] == "461"

    # Hent frisk reference i forsøg på at undgå HTTP 409 Conflict
    suppliers = organizations_client.get_suppliers()
    supplier = [x for x in suppliers if x["name"] == "Testleverandør Supporten Træning"][0]
    assert supplier is not None
    
    resolved_supplier = citizens_client.resolve_reference(supplier)    
    resolved_supplier["address"]["administrativeAreaCode"] = ""
    
    updated_supplier = organizations_client.update_supplier(resolved_supplier)
    assert updated_supplier is not None
    assert updated_supplier["address"]["administrativeAreaCode"] == ""

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

def test_citizen_organization_relations(organizations_client: OrganizationsClient, test_citizen: dict):
    organization_name = "Testorganisation Supporten Dag"
    organizations = organizations_client.get_organizations_by_citizen(test_citizen)
    filtered_organization = next(
        (rel for rel in organizations if rel["organization"]["name"] == organization_name),
        None
    )

    if filtered_organization is not None:
        organizations_client.remove_citizen_from_organization(dict(filtered_organization))
    
    organizations = organizations_client.get_organizations_by_citizen(test_citizen)
    filtered_organization = next(
        (rel for rel in organizations if rel["organization"]["name"] == organization_name),
        None
    )

    assert filtered_organization is None   
    
    organization = organizations_client.get_organization_by_name(organization_name)

    assert organization is not None
    organizations_client.add_citizen_to_organization(test_citizen, organization)

    organizations = organizations_client.get_organizations_by_citizen(test_citizen)
    filtered_organization = next(
        (rel for rel in organizations if rel["organization"]["name"] == organization_name),
        None
    )    
    
    assert filtered_organization is not None