import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.functionality.indsatser import IndsatsClient
from kmd_nexus_client.functionality.borgere import (BorgerClient, filter_references)


def test_hent_indsats_elementer(borgere_client: BorgerClient, indsats_client: IndsatsClient, test_borger: dict):
    """Test hent_indsats_elementer Danish function."""
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None, "Pathway should not be None"
    references = borgere_client.hent_referencer(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = borgere_client.client.hent_fra_reference(references[0])
    
    assert resolved is not None    
    assert resolved["name"] == references[0]["name"]

    elementer = indsats_client.hent_indsats_elementer(resolved)

    assert elementer is not None


def test_backward_compatibility_grants_client(borgere_client: BorgerClient, grants_client, test_borger: dict):
    """Test that GrantsClient backward compatibility works."""
    from kmd_nexus_client.functionality.indsatser import GrantsClient
    
    # Verify grants_client is a GrantsClient instance
    assert isinstance(grants_client, GrantsClient)
    
    # Test that old method names still work
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None, "Pathway should not be None"
    references = borgere_client.hent_referencer(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    if len(references) > 0:
        resolved = borgere_client.client.hent_fra_reference(references[0])
        
        # Test the old method name
        elements = grants_client.get_grant_elements(resolved)
        assert elements is not None


def test_indsats_client_methods_exist(indsats_client: IndsatsClient):
    """Test that all Danish methods exist on IndsatsClient."""
    # Check that all methods exist
    assert hasattr(indsats_client, 'rediger_indsats')
    assert hasattr(indsats_client, 'hent_indsats_elementer')
    assert hasattr(indsats_client, 'opret_indsats')
    assert hasattr(indsats_client, 'hent_indsats_referencer')
    assert hasattr(indsats_client, 'hent_indsats')
    assert hasattr(indsats_client, 'filtrer_indsats_referencer')
    
    # Check that they are callable
    assert callable(indsats_client.rediger_indsats)
    assert callable(indsats_client.hent_indsats_elementer)
    assert callable(indsats_client.opret_indsats)
    assert callable(indsats_client.hent_indsats_referencer)
    assert callable(indsats_client.hent_indsats)
    assert callable(indsats_client.filtrer_indsats_referencer)


def test_hent_indsatser_referenser(indsats_client: IndsatsClient, test_borger: dict):
    """Test hent_indsatser_referencer Danish function."""
    # Get grant references using Danish method
    indsats_referenser = indsats_client.hent_indsats_referencer(
        test_borger,
        forløbsnavn="- Alt",
        inkluder_indsats_pakker=False
    )
    
    # Should return a list (could be empty)
    assert isinstance(indsats_referenser, list)


def test_filtrer_indsats_referenser_empty_list(indsats_client: IndsatsClient):
    """Test filtrer_indsats_referenser with empty input."""
    # Test filtering empty list
    filtered = indsats_client.filtrer_indsats_referencer(
        [],
        kun_aktive=True,
        leverandør_navn=""
    )
    
    assert filtered == []


def test_filtrer_indsats_referencer_with_mock_data(indsats_client: IndsatsClient):
    """Test filtrer_indsats_referencer with mock data."""
    # Create mock grant references
    mock_referenser = [
        {
            "workflowState": {"name": "Bestilt"},
            "additionalInfo": []
        },
        {
            "workflowState": {"name": "Afsluttet"},
            "additionalInfo": []
        },
        {
            "workflowState": {"name": "Bevilliget"},
            "additionalInfo": [
                {"key": "Something"},
                {"key": "Else"},
                {"key": "Leverandør", "value": "Test Leverandør"}
            ]
        }
    ]
    
    # Test filtering for active only
    aktive = indsats_client.filtrer_indsats_referencer(
        mock_referenser,
        kun_aktive=True,
        leverandør_navn=""
    )
    
    # Should exclude "Afsluttet" 
    assert len(aktive) == 2
    assert all(ref["workflowState"]["name"] != "Afsluttet" for ref in aktive)
    
    # Test filtering by supplier
    med_leverandør = indsats_client.filtrer_indsats_referencer(
        mock_referenser,
        kun_aktive=False,
        leverandør_navn="Test Leverandør"
    )
    
    # Should only include the one with matching supplier
    assert len(med_leverandør) == 1
    assert med_leverandør[0]["workflowState"]["name"] == "Bevilliget"


def test_hent_indsats_error_handling(indsats_client: IndsatsClient):
    """Test hent_indsats error handling."""
    # Test with invalid reference
    with pytest.raises(ValueError, match="Input er ikke en gyldig indsats reference"):
        indsats_client.hent_indsats({})
    
    # Test with unknown reference type
    with pytest.raises(ValueError, match="Ukendt reference type"):
        indsats_client.hent_indsats({"type": "unknownType"})


def test_grants_to_indsats_inheritance():
    """Test that GrantsClient is an alias for IndsatsClient."""
    from kmd_nexus_client.functionality.indsatser import IndsatsClient, GrantsClient
    
    # Check that they are the same class
    assert GrantsClient is IndsatsClient


def test_manager_provides_both_properties():
    """Test that NexusClientManager provides both grants and indsats properties."""
    from kmd_nexus_client.manager import NexusClientManager
    
    # Check that manager has both properties
    assert hasattr(NexusClientManager, 'grants')
    assert hasattr(NexusClientManager, 'indsats')


def test_old_english_method_names_work(borgere_client: BorgerClient, indsats_client: IndsatsClient, test_borger: dict):
    """Test that old English method names still work via aliases."""
    citizen = test_borger
    pathway = borgere_client.hent_visning(citizen)
    assert pathway is not None, "Pathway should not be None"
    references = borgere_client.hent_referencer(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    if len(references) > 0:
        resolved = borgere_client.client.hent_fra_reference(references[0])
        
        # Test the old English method name works
        elements = indsats_client.get_grant_elements(resolved)
        assert elements is not None
        
        # Test that it returns the same result as the Danish method
        elementer = indsats_client.hent_indsats_elementer(resolved)
        assert elements == elementer