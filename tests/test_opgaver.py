import pytest

from datetime import date, timedelta

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager



def test_hent_opgave_på_indsats(nexus_manager: NexusClientManager, test_borger: dict,test_indsats: dict):
    resolved_grant_assignments = nexus_manager.opgaver.hent_opgaver(test_indsats)

    assert resolved_grant_assignments is not None

    assert isinstance(resolved_grant_assignments, list)
    assert len(resolved_grant_assignments) > 0, "Ingen opgaver fundet for indsats"


def test_hent_opgave_på_borger(
    nexus_manager: NexusClientManager, test_borger: dict
):
    assignment_id = 5057474  # Test borger opgave - bliver evt. lukket.

    assignment = nexus_manager.opgaver.hent_opgave_for_borger(
        test_borger, assignment_id
    )
    assert assignment is not None
    assert assignment["id"] == assignment_id


def test_opret_opgave(nexus_manager: NexusClientManager, test_indsats: dict):

    assignment = nexus_manager.opgaver.opret_opgave(
        objekt=test_indsats,
        opgave_type="Tværfagligt samarbejde",
        titel="Test assignment fra RPA - 2",
        ansvarlig_organisation="Testorganisation Supporten Aften",
        start_dato=date.today(),
        forfald_dato=date.today() + timedelta(days=3),
    )

    assert assignment is not None

def test_rediger_opgave(nexus_manager: NexusClientManager, test_borger: dict):
    opgave_id = 5057474  # Test borger opgave - bliver evt. lukket.
    opgave = nexus_manager.opgaver.hent_opgave_for_borger(test_borger, opgave_id)
    assert opgave is not None
    assert opgave["id"] == opgave_id

    opgave["title"] = "Test opgave fra RPA - dansk redigeret"
    nexus_manager.opgaver.rediger_opgave(opgave)

    opgave_id = 5057474  # Test borger opgave - bliver evt. lukket.
    opgave = nexus_manager.opgaver.hent_opgave_for_borger(test_borger, opgave_id)
    assert opgave is not None
    assert opgave["title"] == "Test opgave fra RPA - dansk redigeret"


# Test error handling
def test_hent_opgaver_missing_link(nexus_manager: NexusClientManager):
    """Test hent_opgaver with missing availableAssignmentTypes link."""
    mock_objekt = {"id": "test-id", "_links": {}}

    with pytest.raises(
        ValueError, match="Objekt indeholder ikke availableAssignmentTypes link"
    ):
        nexus_manager.opgaver.hent_opgaver(mock_objekt)


def test_hent_opgavetyper(nexus_manager: NexusClientManager, test_borger: dict, test_indsats: dict):
    """Test hent_opgavetyper Danish function."""

    if "availableAssignmentTypes" not in test_indsats.get("_links", {}):
        pytest.skip("Det opløste objekt understøtter ikke opgaver")

    # Test the Danish method
    opgavetyper = nexus_manager.opgaver.hent_opgavetyper(test_indsats)
    assert opgavetyper is not None
    assert isinstance(opgavetyper, list)
    if opgavetyper:  # If there are assignment types
        # Check that each assignment type has expected structure
        for opgavetype in opgavetyper:
            assert "name" in opgavetype
            assert "_links" in opgavetype


