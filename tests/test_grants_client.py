import pytest

from datetime import datetime, timezone
from .fixtures import organizations_client, base_client, test_citizen, citizens_client, grants_client # noqa
from kmd_nexus_client.functionality.grants import GrantsClient, update_grant_elements
from kmd_nexus_client.functionality.borgere import (CitizensClient, filter_references)

# def test_edit_grant(citizens_client: CitizensClient, grants_client: GrantsClient, test_citizen: dict):
#     citizen = test_citizen
#     pathway = citizens_client.get_citizen_pathway(citizen)
#     references = citizens_client.get_citizen_pathway_references(pathway)

#     # TODO: Create a new basket_grant

#     references = filter_references(
#         references,
#         path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
#         active_pathways_only=True,
#     )

#     assert len(references) > 0
    
#     resolved = citizens_client.resolve_reference(references[0])
    
#     assert resolved is not None    
#     assert resolved["name"] == references[0]["name"]
    
#     # TODO: Kill/improve this internal function
#     field_updates = {
#         "description": "Test data",
#         "entryDate": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+0000'
#     }
    
#     # Update the grant
#     grant = grants_client.edit_grant(resolved, field_updates, "Ændr")

#     # Check that the grant was updated
#     assert grant is not None
    
#     updated_element = next((e for e in grant["savedGrant"]["currentElements"] if e["type"] == "description"), None)
#     assert updated_element is not None
#     assert updated_element["text"] == field_updates["description"]


def test_get_grant_elements(citizens_client: CitizensClient, grants_client: GrantsClient, test_citizen: dict):
    citizen = test_citizen
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = citizens_client.resolve_reference(references[0])
    
    assert resolved is not None    
    assert resolved["name"] == references[0]["name"]

    elements = grants_client.get_grant_elements(resolved)

    assert elements is not None
