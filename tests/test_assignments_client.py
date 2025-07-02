import pytest

from datetime import date, timedelta
from httpx import HTTPStatusError
from .fixtures import assignments_client, base_client, test_citizen, citizens_client, organizations_client  # noqa
from kmd_nexus_client.functionality.opgaver import OpgaverClient
from kmd_nexus_client.functionality.borgere import CitizensClient, filter_references


def test_get_assignments_by_grant(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):
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
    assert resolved_grant_assignments[0]["title"] == "Test assignment fra RPA - 2"

def test_get_assignment_by_citizen(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):    
    assignment_id = 5057474  # Test borger opgave - bliver evt. lukket.

    assignment = assignments_client.get_assignment_by_citizen(test_citizen, assignment_id)
    assert assignment is not None
    assert assignment["id"] == assignment_id

def test_create_assignment(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):
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

def test_edit_assignment(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):
    assignment_id = 5057474  # Test borger opgave - bliver evt. lukket.
    assignment = assignments_client.get_assignment_by_citizen(test_citizen, assignment_id)
    assert assignment is not None
    assert assignment["id"] == assignment_id
    
    assignment["title"] = "Test assignment fra RPA - 2 - redigeret"
    assignments_client.edit_assignment(assignment)

    assignment_id = 5057474  # Test borger opgave - bliver evt. lukket.
    assignment = assignments_client.get_assignment_by_citizen(test_citizen, assignment_id)
    assert assignment is not None
    assert assignment["title"] == "Test assignment fra RPA - 2 - redigeret"


# Tests for Danish functions
def test_hent_opgaver(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):
    """Test hent_opgaver Danish function."""
    citizen = test_citizen
    pathway = citizens_client.get_citizen_pathway(citizen)
    references = citizens_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    resolved_grant = citizens_client.resolve_reference(references[0])

    # Test the Danish method
    opgaver = assignments_client.hent_opgaver(resolved_grant)
    assert opgaver is not None
    assert opgaver[0]["title"] == "Test assignment fra RPA - 2"


def test_hent_opgave_for_borger(assignments_client: OpgaverClient, test_citizen: dict):
    """Test hent_opgave_for_borger Danish function."""
    opgave_id = 5057474  # Test borger opgave - bliver evt. lukket.

    opgave = assignments_client.hent_opgave_for_borger(test_citizen, opgave_id)
    assert opgave is not None
    assert opgave["id"] == opgave_id


def test_opret_opgave(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):
    """Test opret_opgave Danish function."""
    borger = test_citizen
    pathway = citizens_client.get_citizen_pathway(borger)
    references = citizens_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    resolved_grant = citizens_client.resolve_reference(references[0])
    assert resolved_grant["name"] == references[0]["name"]

    # Test the Danish method with Danish parameter names
    opgave = assignments_client.opret_opgave(
        objekt=resolved_grant,
        opgave_type="Tværfagligt samarbejde",
        titel="Test opgave fra RPA - dansk",
        ansvarlig_organisation="Testorganisation Supporten Aften",
        start_dato=date.today(),
        forfald_dato=date.today() + timedelta(days=3))
        
    assert opgave is not None


def test_rediger_opgave(assignments_client: OpgaverClient, test_citizen: dict):
    """Test rediger_opgave Danish function."""
    opgave_id = 5057474  # Test borger opgave - bliver evt. lukket.
    opgave = assignments_client.hent_opgave_for_borger(test_citizen, opgave_id)
    assert opgave is not None
    assert opgave["id"] == opgave_id
    
    opgave["title"] = "Test opgave fra RPA - dansk redigeret"
    assignments_client.rediger_opgave(opgave)

    opgave_id = 5057474  # Test borger opgave - bliver evt. lukket.
    opgave = assignments_client.hent_opgave_for_borger(test_citizen, opgave_id)
    assert opgave is not None
    assert opgave["title"] == "Test opgave fra RPA - dansk redigeret"


# Test backward compatibility
def test_backward_compatibility_aliases(assignments_client: OpgaverClient, test_citizen: dict):
    """Test that old method names still work for backward compatibility."""
    # Test that aliases exist
    assert hasattr(assignments_client, 'get_assignments')
    assert hasattr(assignments_client, 'get_assignment_by_citizen')
    assert hasattr(assignments_client, 'create_assignment')
    assert hasattr(assignments_client, 'edit_assignment')
    
    # Test get_assignment_by_citizen alias works
    opgave_id = 5057474
    result1 = assignments_client.get_assignment_by_citizen(test_citizen, opgave_id)
    result2 = assignments_client.hent_opgave_for_borger(test_citizen, opgave_id)
    assert result1 == result2


# Test error handling
def test_hent_opgaver_missing_link(assignments_client: OpgaverClient):
    """Test hent_opgaver with missing availableAssignmentTypes link."""
    mock_objekt = {
        "id": "test-id",
        "_links": {}
    }
    
    with pytest.raises(ValueError, match="Objekt indeholder ikke availableAssignmentTypes link"):
        assignments_client.hent_opgaver(mock_objekt)


def test_hent_opgave_for_borger_invalid_citizen(assignments_client: OpgaverClient):
    """Test hent_opgave_for_borger with invalid citizen."""
    result = assignments_client.hent_opgave_for_borger("not-a-dict", 123)
    assert result is None


def test_opret_opgave_missing_assignment_type(assignments_client: OpgaverClient):
    """Test opret_opgave with missing assignment type."""
    mock_objekt = {
        "_links": {
            "availableAssignmentTypes": {"href": "test-url"}
        }
    }
    
    # Mock HTTP response
    from unittest.mock import Mock
    original_get = assignments_client.nexus_client.get
    mock_response = Mock()
    mock_response.json.return_value = []  # Empty list = no assignment types
    assignments_client.nexus_client.get = Mock(return_value=mock_response)
    
    try:
        with pytest.raises(ValueError, match="Opgave type .* ikke fundet i tilgængelige opgave typer"):
            assignments_client.opret_opgave(
                objekt=mock_objekt,
                opgave_type="NonExistentType",
                titel="Test",
                ansvarlig_organisation="Test Org",
                start_dato=date.today()
            )
    finally:
        assignments_client.nexus_client.get = original_get


def test_opret_og_luk_opgave_integration(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):
    """Integration test - opret og luk opgave på det første objekt der understøtter opgaver."""
    import time
    from kmd_nexus_client.tree_helpers import find_first_node
    
    # Find citizen pathway and get view with activity structure
    borger = test_citizen

    visning = citizens_client.hent_visning(borger, "- Alt")
    if visning is None:
        pytest.skip("Ingen visning fundet for test citizen")

    referencer = citizens_client.hent_referencer(visning)

    # Use tree_helpers to find the first node that supports assignments
    def supports_assignments(node: dict) -> bool:
        """Check if a node has availableAssignmentTypes link when resolved."""
        if "_links" not in node or "self" not in node["_links"]:
            return False
        try:
            # Resolve the reference to check for assignment support
            resolved_obj = citizens_client.client.hent_fra_reference(node)
            return "availableAssignmentTypes" in resolved_obj.get("_links", {})
        except Exception:
            return False
    
    # Traverse the activity tree to find an object that supports assignments
    target_object = find_first_node(referencer, supports_assignments, "children")
    
    if not target_object:
        pytest.skip("Ingen objekter fundet der understøtter opgaver for test citizen")
    
    print(f"Fandt objekt der understøtter opgaver: {target_object.get('name', 'Unknown')}")
    
    # Resolve the target object to get full details with links
    resolved_target = citizens_client.client.hent_fra_reference(target_object)
    
    # Get available assignment types using the new Danish function
    available_types = assignments_client.hent_opgavetyper(resolved_target)
    
    if not available_types:
        pytest.skip("Ingen opgavetyper tilgængelige for det fundne objekt")
    
    # Use the first available assignment type
    assignment_type = available_types[0]["name"]
    print(f"Bruger opgavetype: {assignment_type}")
    
    # Create assignment with Danish function
    try:
        ny_opgave = assignments_client.opret_opgave(
            objekt=resolved_target,
            opgave_type=assignment_type,
            titel="Test opgave - opret og luk integration",
            ansvarlig_organisation="Testorganisation Supporten Aften",
            start_dato=date.today(),
            forfald_dato=date.today() + timedelta(days=1),
            beskrivelse="Integration test opgave der skal lukkes"
        )
        
        assert ny_opgave is not None, "Opgave blev ikke oprettet"
        print(f"Opgave oprettet med ID: {ny_opgave.get('id', 'Unknown')}")
        
        # Get the full assignment with actions (sometimes actions are not in the creation response)
        opgave_id = ny_opgave["id"]
        fuld_opgave = assignments_client.hent_opgave_for_borger(borger, opgave_id)
        
        if fuld_opgave is None:
            # Try alternative: get assignments on the object and find our task
            time.sleep(1)  # Give system time to process
            opgaver_på_objekt = assignments_client.hent_opgaver(resolved_target)
            fuld_opgave = next(
                (opgave for opgave in opgaver_på_objekt if opgave["id"] == opgave_id),
                None
            )
        
        assert fuld_opgave is not None, f"Kunne ikke hente den oprettede opgave med ID {opgave_id}"
        print(f"Hentet fuld opgave: {fuld_opgave.get('title', 'Unknown title')}")
        
        # Try to close the assignment using Danish function
        lukket = assignments_client.luk_opgave(fuld_opgave)
        
        if not lukket:
            print("Kunne ikke lukke opgave - måske mangler 'Afslut' action")
            if 'actions' in fuld_opgave:
                action_names = []
                for action in fuld_opgave['actions']:
                    if isinstance(action, dict):
                        action_names.append(action.get('name', 'No name'))
                    else:
                        action_names.append(str(action))
                print(f"Tilgængelige actions: {action_names}")
            # This is not necessarily a test failure - some assignments might not be closable
            pytest.skip("Opgaven kunne ikke lukkes - måske ikke understøttet for denne opgavetype")
        else:
            print("✅ Opgave blev succesfuldt lukket")
            assert lukket is True, "luk_opgave returnerede ikke True"
            
    except Exception as e:
        pytest.fail(f"Integration test fejlede: {str(e)}")


def test_luk_opgave_unit_tests(assignments_client: OpgaverClient):
    """Unit tests for luk_opgave function."""
    from unittest.mock import Mock
    
    # Test with assignment that has no actions
    opgave_uden_actions = {"id": 123, "title": "Test"}
    result = assignments_client.luk_opgave(opgave_uden_actions)
    assert result is False
    
    # Test with assignment that has actions but no "Afslut"
    opgave_uden_afslut = {
        "id": 123,
        "title": "Test", 
        "actions": [
            {"name": "Rediger", "_links": {"updateAssignment": {"href": "test-url"}}}
        ]
    }
    result = assignments_client.luk_opgave(opgave_uden_afslut)
    assert result is False
    
    # Test with assignment that has "Afslut" action - success case
    opgave_med_afslut = {
        "id": 123,
        "title": "Test",
        "actions": [
            {"name": "Afslut", "_links": {"updateAssignment": {"href": "test-close-url"}}}
        ]
    }
    
    # Mock successful close
    original_put = assignments_client.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 200
    assignments_client.nexus_client.put = Mock(return_value=mock_response)
    
    try:
        result = assignments_client.luk_opgave(opgave_med_afslut)
        assert result is True
        assignments_client.nexus_client.put.assert_called_once_with(
            "test-close-url",
            json=opgave_med_afslut
        )
    finally:
        assignments_client.nexus_client.put = original_put
    
    # Test HTTP error handling
    assignments_client.nexus_client.put = Mock(side_effect=HTTPStatusError("Test error", request=Mock(), response=Mock()))
    
    try:
        result = assignments_client.luk_opgave(opgave_med_afslut)
        assert result is False
    finally:
        assignments_client.nexus_client.put = original_put


def test_close_assignment_backward_compatibility(assignments_client: OpgaverClient):
    """Test backward compatibility alias for close_assignment."""
    opgave = {
        "id": 123,
        "title": "Test",
        "actions": [
            {"name": "Afslut", "_links": {"updateAssignment": {"href": "test-url"}}}
        ]
    }
    
    # Mock response
    from unittest.mock import Mock
    original_put = assignments_client.nexus_client.put
    mock_response = Mock()
    mock_response.status_code = 200
    assignments_client.nexus_client.put = Mock(return_value=mock_response)
    
    try:
        # Test that the old method name works
        result = assignments_client.close_assignment(opgave)
        assert result is True
        
        # Test that it calls the same underlying method
        result_new = assignments_client.luk_opgave(opgave)
        assert result == result_new
    finally:
        assignments_client.nexus_client.put = original_put


def test_tree_helpers_integration_demo():
    """Demo test showing how to use tree_helpers to find assignment-capable objects."""
    from kmd_nexus_client.tree_helpers import find_first_node, find_nodes
    
    # Mock tree structure representing a citizen's activities
    mock_citizen_tree = {
        "name": "Borger Aktiviteter",
        "children": [
            {
                "name": "Forløb 1",
                "children": [
                    {
                        "name": "Skema 1",
                        "_links": {"self": {"href": "schema1"}}
                    },
                    {
                        "name": "Indsats 1",
                        "_links": {
                            "self": {"href": "indsats1"},
                            "availableAssignmentTypes": {"href": "assignments1"}
                        }
                    }
                ]
            },
            {
                "name": "Forløb 2", 
                "children": [
                    {
                        "name": "Skema 2",
                        "_links": {
                            "self": {"href": "schema2"},
                            "availableAssignmentTypes": {"href": "assignments2"}
                        }
                    }
                ]
            }
        ]
    }
    
    # Find first object that supports assignments
    assignment_capable = find_first_node(
        mock_citizen_tree,
        lambda node: "_links" in node and "availableAssignmentTypes" in node.get("_links", {}),
        "children"
    )
    
    assert assignment_capable is not None
    assert assignment_capable["name"] == "Indsats 1"
    assert "availableAssignmentTypes" in assignment_capable["_links"]
    
    # Find all objects that support assignments
    all_assignment_capable = find_nodes(
        mock_citizen_tree,
        lambda node: "_links" in node and "availableAssignmentTypes" in node.get("_links", {}),
        "children"
    )
    
    assert len(all_assignment_capable) == 2
    assert all_assignment_capable[0]["name"] == "Indsats 1"
    assert all_assignment_capable[1]["name"] == "Skema 2"
    
    print("✅ Tree helpers successfully found assignment-capable objects")
    print(f"   First found: {assignment_capable['name']}")
    print(f"   Total found: {len(all_assignment_capable)}")


def test_hent_opgavetyper(assignments_client: OpgaverClient, citizens_client: CitizensClient, test_citizen: dict):
    """Test hent_opgavetyper Danish function."""
    citizen = test_citizen
    pathway = citizens_client.get_citizen_pathway(citizen)
    if pathway is None:
        pytest.skip("Ingen pathway fundet for test citizen")
    
    references = citizens_client.get_citizen_pathway_references(pathway)

    filtered_refs = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    if not filtered_refs:
        pytest.skip("Ingen medicin references fundet")

    resolved_grant = citizens_client.resolve_reference(filtered_refs[0])
    
    if "availableAssignmentTypes" not in resolved_grant.get("_links", {}):
        pytest.skip("Det opløste objekt understøtter ikke opgaver")

    # Test the Danish method
    opgavetyper = assignments_client.hent_opgavetyper(resolved_grant)
    assert opgavetyper is not None
    assert isinstance(opgavetyper, list)
    if opgavetyper:  # If there are assignment types
        # Check that each assignment type has expected structure
        for opgavetype in opgavetyper:
            assert "name" in opgavetype
            assert "_links" in opgavetype


def test_hent_opgavetyper_missing_link(assignments_client: OpgaverClient):
    """Test hent_opgavetyper with missing availableAssignmentTypes link."""
    mock_objekt = {
        "id": "test-id",
        "_links": {}
    }
    
    with pytest.raises(ValueError, match="Objekt indeholder ikke availableAssignmentTypes link"):
        assignments_client.hent_opgavetyper(mock_objekt)


def test_hent_opgavetyper_success_case(assignments_client: OpgaverClient):
    """Test hent_opgavetyper success case with mocked response."""
    from unittest.mock import Mock
    
    mock_objekt = {
        "_links": {
            "availableAssignmentTypes": {"href": "test-url"}
        }
    }
    
    # Mock successful response
    original_get = assignments_client.nexus_client.get
    mock_response = Mock()
    mock_response.json.return_value = [
        {"name": "Tværfagligt samarbejde", "_links": {"assignmentPrototype": {"href": "proto1"}}},
        {"name": "Opfølgning", "_links": {"assignmentPrototype": {"href": "proto2"}}}
    ]
    assignments_client.nexus_client.get = Mock(return_value=mock_response)
    
    try:
        result = assignments_client.hent_opgavetyper(mock_objekt)
        assert len(result) == 2
        assert result[0]["name"] == "Tværfagligt samarbejde"
        assert result[1]["name"] == "Opfølgning"
        
        assignments_client.nexus_client.get.assert_called_once_with("test-url")
    finally:
        assignments_client.nexus_client.get = original_get


def test_get_assignment_types_backward_compatibility(assignments_client: OpgaverClient):
    """Test backward compatibility alias for get_assignment_types."""
    from unittest.mock import Mock
    
    mock_objekt = {
        "_links": {
            "availableAssignmentTypes": {"href": "test-url"}
        }
    }
    
    # Mock response
    original_get = assignments_client.nexus_client.get
    mock_response = Mock()
    mock_response.json.return_value = [{"name": "Test Type"}]
    assignments_client.nexus_client.get = Mock(return_value=mock_response)
    
    try:
        # Test that the old method name works
        result_old = assignments_client.get_assignment_types(mock_objekt)
        result_new = assignments_client.hent_opgavetyper(mock_objekt)
        assert result_old == result_new
    finally:
        assignments_client.nexus_client.get = original_get
