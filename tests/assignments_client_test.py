import pytest

from datetime import date, timedelta
from .fixtures import assignments_client, base_client, test_citizen, citizens_client, organizations_client  # noqa
from kmd_nexus_client.functionality.assignments import AssignmentsClient
from kmd_nexus_client.functionality.citizens import CitizensClient, filter_references


def test_get_assignments_by_grant(assignments_client: AssignmentsClient, citizens_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    resolved_grant = citizens_client.resolve_reference(references[0])

    resolved_grant_assignments = assignments_client.get_assignments(resolved_grant)
    assert resolved_grant_assignments is not None
    assert resolved_grant_assignments[0]["title"] == "Tværfagligt samarbejde - RPA TEST IGNORER"

def test_create_assignment(assignments_client: AssignmentsClient, citizens_client: CitizensClient, test_citizen: dict):
    citizen = test_citizen
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    resolved_grant = citizens_client.resolve_reference(references[0])
    assert resolved_grant["name"] == references[0]["name"]

    assignment = assignments_client.create_assignment(
        object=resolved_grant,
        assignment_type="Tværfagligt samarbejde",
        title="Test assignment fra RPA - 2",
        responsible_organization="Testorganisation Supporten Aften",
        start_date=date.today(),
        due_date=date.today() + timedelta(days=3))
        
    assert assignment is not None