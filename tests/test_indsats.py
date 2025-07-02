import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.functionality.indsatser import IndsatsClient
from kmd_nexus_client.functionality.borgere import (CitizensClient, filter_references)


def test_hent_indsats_elementer(borgere_client: CitizensClient, indsats_client: IndsatsClient, test_citizen: dict):
    """Test hent_indsats_elementer Danish function."""
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)
    references = borgere_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    assert len(references) > 0
    
    resolved = borgere_client.resolve_reference(references[0])
    
    assert resolved is not None    
    assert resolved["name"] == references[0]["name"]

    elementer = indsats_client.hent_indsats_elementer(resolved)

    assert elementer is not None


def test_backward_compatibility_grants_client(borgere_client: CitizensClient, grants_client, test_citizen: dict):
    """Test that GrantsClient backward compatibility works."""
    from kmd_nexus_client.functionality.indsatser import GrantsClient
    
    # Verify grants_client is a GrantsClient instance
    assert isinstance(grants_client, GrantsClient)
    
    # Test that old method names still work
    citizen = test_citizen
    pathway = borgere_client.get_citizen_pathway(citizen)
    references = borgere_client.get_citizen_pathway_references(pathway)

    references = filter_references(
        references,
        path="/Sundhedsfagligt grundforløb/FSIII/Indsatser/Medicin%",
        active_pathways_only=True,
    )

    if len(references) > 0:
        resolved = borgere_client.resolve_reference(references[0])
        
        # Test the old method name
        elements = grants_client.get_grant_elements(resolved)
        assert elements is not None


def test_indsats_client_methods_exist(indsats_client: IndsatsClient):
    """Test that all Danish methods exist on IndsatsClient."""
    # Check that all methods exist
    assert hasattr(indsats_client, 'rediger_indsats')
    assert hasattr(indsats_client, 'hent_indsats_elementer')
    assert hasattr(indsats_client, 'opret_indsats')
    assert hasattr(indsats_client, 'hent_indsatser_referencer')
    assert hasattr(indsats_client, 'hent_indsats')
    assert hasattr(indsats_client, 'filtrer_indsatser_referencer')
    
    # Check that they are callable
    assert callable(indsats_client.rediger_indsats)
    assert callable(indsats_client.hent_indsats_elementer)
    assert callable(indsats_client.opret_indsats)
    assert callable(indsats_client.hent_indsatser_referencer)
    assert callable(indsats_client.hent_indsats)
    assert callable(indsats_client.filtrer_indsatser_referencer)


def test_hent_indsatser_referencer(borgere_client: CitizensClient, indsats_client: IndsatsClient, test_citizen: dict):
    """Test hent_indsatser_referencer Danish function."""
    # Get grant references using Danish method
    indsatser_referencer = indsats_client.hent_indsatser_referencer(
        test_citizen,
        forløbsnavn="- Alt",
        inkluder_indsats_pakker=False
    )
    
    # Should return a list (could be empty)
    assert isinstance(indsatser_referencer, list)


def test_filtrer_indsatser_referencer_empty_list(indsats_client: IndsatsClient):
    """Test filtrer_indsatser_referencer with empty input."""
    # Test filtering empty list
    filtered = indsats_client.filtrer_indsatser_referencer(
        [],
        kun_aktive=True,
        leverandør_navn=""
    )
    
    assert filtered == []


def test_filtrer_indsatser_referencer_with_mock_data(indsats_client: IndsatsClient):
    """Test filtrer_indsatser_referencer with mock data."""
    # Create mock grant references
    mock_referencer = [
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
    aktive = indsats_client.filtrer_indsatser_referencer(
        mock_referencer,
        kun_aktive=True,
        leverandør_navn=""
    )
    
    # Should exclude "Afsluttet" 
    assert len(aktive) == 2
    assert all(ref["workflowState"]["name"] != "Afsluttet" for ref in aktive)
    
    # Test filtering by supplier
    med_leverandør = indsats_client.filtrer_indsatser_referencer(
        mock_referencer,
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