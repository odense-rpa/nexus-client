"""
Tests for IndsatsClient._fill_grant_elements method.

This module tests the grant element filling functionality with various field types
using realistic data from the grant prototype fixture.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch


def get_test_element(grant_prototype_data, element_type, as_list=True):
    """Extract and copy an element from grant prototype data for testing."""
    element = next(
        (e for e in grant_prototype_data["currentElements"] if e["type"] == element_type),
        None
    )
    assert element is not None, f"{element_type} element not found in prototype"
    
    if as_list:
        return [element.copy()]
    return element.copy()


def test_text_fields_success_and_exception(nexus_manager, grant_prototype_data):
    """Test text field handling - personReference field."""
    client = nexus_manager.indsats
    
    # Get test element
    elements = get_test_element(grant_prototype_data, "personReference")
    
    # Test success case
    fields = {"personReference": "test-person-123"}
    client._fill_grant_elements(elements, fields)
    assert elements[0]["text"] == "test-person-123"
    
    # Test exception case - non-string value
    elements = get_test_element(grant_prototype_data, "personReference")
    fields = {"personReference": 12345}
    
    with pytest.raises(ValueError, match="Field 'personReference' expects a string value"):
        client._fill_grant_elements(elements, fields)


def test_date_fields_success_and_exception(nexus_manager, grant_prototype_data):
    """Test date field handling - plannedDate field."""
    client = nexus_manager.indsats
    
    # Get test element
    elements = get_test_element(grant_prototype_data, "plannedDate")
    
    # Test success case - naive datetime
    naive_dt = datetime(2025, 1, 15, 10, 30, 0)
    fields = {"plannedDate": naive_dt}
    client._fill_grant_elements(elements, fields)
    
    # Should be converted to UTC ISO format
    assert elements[0]["date"].endswith("Z")
    assert "2025-01-15" in elements[0]["date"]
    
    # Test success case - timezone-aware datetime
    elements = get_test_element(grant_prototype_data, "plannedDate")
    aware_dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    fields = {"plannedDate": aware_dt}
    client._fill_grant_elements(elements, fields)
    
    assert elements[0]["date"] == "2025-01-15T10:30:00Z"
    
    # Test exception case - non-datetime value
    elements = get_test_element(grant_prototype_data, "plannedDate")
    fields = {"plannedDate": "2025-01-15"}
    
    with pytest.raises(ValueError, match="Field 'plannedDate' expects a date value"):
        client._fill_grant_elements(elements, fields)


def test_value_with_possible_values_success_and_exception(nexus_manager, grant_prototype_data):
    """Test value field with possibleValues - payor field."""
    client = nexus_manager.indsats
    
    # Get test element
    elements = get_test_element(grant_prototype_data, "payor")
    
    # Test success case - valid value
    fields = {"payor": "CITIZEN"}
    client._fill_grant_elements(elements, fields)
    assert elements[0]["value"] == "CITIZEN"
    
    # Test exception case - invalid value
    elements = get_test_element(grant_prototype_data, "payor")
    fields = {"payor": "INVALID_PAYOR"}
    
    with pytest.raises(ValueError, match="Value 'INVALID_PAYOR' not in possible values for field 'payor'"):
        client._fill_grant_elements(elements, fields)
    
    # Test exception case - non-string value
    elements = get_test_element(grant_prototype_data, "payor")
    fields = {"payor": 123}
    
    with pytest.raises(ValueError, match="Field 'payor' expects a string value"):
        client._fill_grant_elements(elements, fields)


def test_boolean_value_fields_success_and_exception(nexus_manager, grant_prototype_data):
    """Test boolean value field - denmarkStatisticRareDisability field."""
    client = nexus_manager.indsats
    
    # Get test element
    elements = get_test_element(grant_prototype_data, "denmarkStatisticRareDisability")
    
    # Test success case - True
    fields = {"denmarkStatisticRareDisability": True}
    client._fill_grant_elements(elements, fields)
    assert elements[0]["value"] is True
    
    # Test success case - False
    elements = get_test_element(grant_prototype_data, "denmarkStatisticRareDisability")
    fields = {"denmarkStatisticRareDisability": False}
    client._fill_grant_elements(elements, fields)
    assert elements[0]["value"] is False
    
    # Test exception case - non-boolean value
    elements = get_test_element(grant_prototype_data, "denmarkStatisticRareDisability")
    fields = {"denmarkStatisticRareDisability": "true"}
    
    with pytest.raises(ValueError, match="Field 'denmarkStatisticRareDisability' expects a boolean value"):
        client._fill_grant_elements(elements, fields)


def test_selected_values_success_and_exception(nexus_manager, grant_prototype_data):
    """Test selectedValues field - denmarkStatisticMappingTargetGroup field."""
    client = nexus_manager.indsats
    
    # Get test element
    elements = get_test_element(grant_prototype_data, "denmarkStatisticMappingTargetGroup")
    
    # Test success case - valid list of values
    fields = {"denmarkStatisticMappingTargetGroup": ["1.1.1", "1.1.2"]}
    client._fill_grant_elements(elements, fields)
    assert elements[0]["selectedValues"] == ["1.1.1", "1.1.2"]
    
    # Test exception case - non-list value
    elements = get_test_element(grant_prototype_data, "denmarkStatisticMappingTargetGroup")
    fields = {"denmarkStatisticMappingTargetGroup": "1.1.1"}
    
    with pytest.raises(ValueError, match="Field 'denmarkStatisticMappingTargetGroup' expects a list of selected values"):
        client._fill_grant_elements(elements, fields)
    
    # Test exception case - invalid value in list
    elements = get_test_element(grant_prototype_data, "denmarkStatisticMappingTargetGroup")
    fields = {"denmarkStatisticMappingTargetGroup": ["INVALID_VALUE"]}
    
    with pytest.raises(ValueError, match="Selected value 'INVALID_VALUE' not in possible values"):
        client._fill_grant_elements(elements, fields)
    
    # Test exception case - non-string in list
    elements = get_test_element(grant_prototype_data, "denmarkStatisticMappingTargetGroup")
    fields = {"denmarkStatisticMappingTargetGroup": [123]}
    
    with pytest.raises(ValueError, match="Selected value '123' in field 'denmarkStatisticMappingTargetGroup' must be a string"):
        client._fill_grant_elements(elements, fields)


def test_decimal_fields_success_and_exception(nexus_manager, grant_prototype_data):
    """Test decimal field - price field."""
    client = nexus_manager.indsats
    
    # Get test element
    elements = get_test_element(grant_prototype_data, "price")
    
    # Test success case - integer value
    fields = {"price": 100}
    client._fill_grant_elements(elements, fields)
    assert elements[0]["decimal"] == 100
    
    # Test success case - float value
    elements = get_test_element(grant_prototype_data, "price")
    fields = {"price": 123.45}
    client._fill_grant_elements(elements, fields)
    assert elements[0]["decimal"] == 123.45
    
    # Test exception case - non-numeric value
    elements = get_test_element(grant_prototype_data, "price")
    fields = {"price": "123.45"}
    
    with pytest.raises(ValueError, match="Field 'price' expects a decimal value"):
        client._fill_grant_elements(elements, fields)


def test_supplier_fields_success_and_exception(nexus_manager, grant_prototype_data):
    """Test supplier field handling."""
    client = nexus_manager.indsats
    
    # Mock the client.client.get method directly
    with patch.object(client.client, 'get') as mock_get:
        # Get test element
        elements = get_test_element(grant_prototype_data, "supplier")
        
        # Test success case
        mock_suppliers_response = Mock()
        mock_suppliers_response.json.return_value = [
            {"id": 1, "name": "Test Supplier", "active": True},
            {"id": 2, "name": "Another Supplier", "active": True}
        ]
        mock_get.return_value = mock_suppliers_response
        
        fields = {"supplier": "Test Supplier"}
        client._fill_grant_elements(elements, fields)
        
        assert elements[0]["supplier"]["name"] == "Test Supplier"
        assert elements[0]["supplier"]["id"] == 1
        
        # Test exception case - supplier not found
        elements = get_test_element(grant_prototype_data, "supplier")
        fields = {"supplier": "Nonexistent Supplier"}
        
        with pytest.raises(ValueError, match="Supplier 'Nonexistent Supplier' not found"):
            client._fill_grant_elements(elements, fields)
        
        # Test exception case - non-string value
        elements = get_test_element(grant_prototype_data, "supplier")
        fields = {"supplier": 123}
        
        with pytest.raises(ValueError, match="Field 'supplier' expects a supplier name"):
            client._fill_grant_elements(elements, fields)


def test_fill_grant_elements_modifies_original_data(nexus_manager, grant_prototype_data):
    """Test that _fill_grant_elements modifies the original data structure by reference."""
    client = nexus_manager.indsats
    
    # Use actual currentElements from prototype (not copies)
    elements = grant_prototype_data["currentElements"]
    
    # Find original text and date elements
    person_ref_element = next(e for e in elements if e["type"] == "personReference")
    planned_date_element = next(e for e in elements if e["type"] == "plannedDate")
    
    # Store original values
    original_text = person_ref_element.get("text")
    original_date = planned_date_element.get("date")
    
    # Apply changes through _fill_grant_elements
    test_date = datetime(2025, 2, 15, 14, 30, 0, tzinfo=timezone.utc)
    fields = {
        "personReference": "test-modified-person-123",
        "plannedDate": test_date
    }
    
    client._fill_grant_elements(elements, fields)
    
    # Verify original data was modified
    assert person_ref_element["text"] == "test-modified-person-123"
    assert planned_date_element["date"] == "2025-02-15T14:30:00Z"
    
    # Verify we actually changed from original values
    assert person_ref_element["text"] != original_text
    assert planned_date_element["date"] != original_date


def test_error_handling_field_not_found_and_unsupported_type(nexus_manager, grant_prototype_data):  # grant_prototype_data not used - testing errors only
    """Test error handling for field not found and unsupported field types."""
    client = nexus_manager.indsats
    
    # Test field not found
    elements = [{"type": "existingField", "text": "test"}]
    fields = {"nonExistentField": "value"}
    
    with pytest.raises(ValueError, match="Field 'nonExistentField' not found in template elements"):
        client._fill_grant_elements(elements, fields)
    
    # Test unsupported field type (field with no known value type)
    unsupported_element = {
        "type": "unknownFieldType",
        "someUnknownProperty": "value"
    }
    elements = [unsupported_element]
    fields = {"unknownFieldType": "someValue"}
    
    with pytest.raises(ValueError, match="Unsupported field type for 'unknownFieldType' in template"):
        client._fill_grant_elements(elements, fields)