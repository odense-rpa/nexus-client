"""
Tests for NexusClientManager functionality.
"""

from unittest.mock import Mock, patch
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.borgere import BorgerClient
from kmd_nexus_client.functionality.organisationer import OrganisationerClient
from kmd_nexus_client.functionality.opgaver import OpgaverClient
from kmd_nexus_client.functionality.indsatser import IndsatsClient
from kmd_nexus_client.functionality.kalender import KalenderClient
from kmd_nexus_client.functionality.forløb import ForløbClient


class TestNexusClientManager:
    """Test the NexusClientManager class."""
    
    def test_manager_initialization(self):
        """Test that the manager initializes correctly."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        assert manager._instance == "test-instance"
        assert manager._client_id == "test-client-id"
        assert manager._client_secret == "test-client-secret"
        # AI safety functionality removed
        
        # All clients should be None initially (lazy loading)
        assert manager._nexus_client is None
        assert manager._borgere_client is None
        assert manager._organisationer_client is None
        assert manager._opgaver_client is None
        assert manager._indsats_client is None
        assert manager._kalender_client is None
        assert manager._forløb_client is None
    
    
    @patch('kmd_nexus_client.manager.NexusClient')
    def test_nexus_client_lazy_loading(self, mock_nexus_client):
        """Test that the base NexusClient is lazy-loaded."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Should not be called yet
        mock_nexus_client.assert_not_called()
        
        # Access nexus_client property
        client = manager.nexus_client
        
        # Should be called now with hook configuration
        expected_call = mock_nexus_client.call_args
        assert expected_call is not None
        args, kwargs = expected_call
        
        # Check required parameters
        assert kwargs["instance"] == "test-instance"
        assert kwargs["client_id"] == "test-client-id"
        assert kwargs["client_secret"] == "test-client-secret"
        
        # Check that configuration parameters are present (defaults)
        assert "timeout" in kwargs
        
        # Second access should return the same instance
        client2 = manager.nexus_client
        assert client is client2
        
        # NexusClient constructor should still only be called once
        assert mock_nexus_client.call_count == 1
    
    @patch('kmd_nexus_client.manager.NexusClient')
    @patch('kmd_nexus_client.manager.BorgerClient')
    def test_citizens_client_lazy_loading(self, mock_borgere_client, mock_nexus_client):
        """Test that the BorgerClient is lazy-loaded via citizens property."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Should not be called yet
        mock_borgere_client.assert_not_called()
        
        # Access citizens property
        citizens = manager.citizens
        
        # Should be called now
        mock_borgere_client.assert_called_once()
        
        # Second access should return the same instance
        citizens2 = manager.citizens
        assert citizens is citizens2
        
        # BorgerClient constructor should still only be called once
        assert mock_borgere_client.call_count == 1
    
    
    @patch('kmd_nexus_client.manager.NexusClient')
    @patch('kmd_nexus_client.manager.KalenderClient')
    def test_kalender_client_dependencies(self, mock_kalender_client, mock_nexus_client):
        """Test that KalenderClient gets the correct dependencies."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Access kalender property
        kalender = manager.kalender
        
        # KalenderClient should be called with only nexus_client (no borgere dependency)
        mock_kalender_client.assert_called_once()
        call_args = mock_kalender_client.call_args[0]
        
        # Only argument should be the nexus client
        assert len(call_args) == 1
        assert call_args[0] == manager.nexus_client
    
    @patch('kmd_nexus_client.manager.NexusClient')
    def test_all_clients_lazy_loading(self, mock_nexus_client):
        """Test that all functionality clients are lazy-loaded."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Access all client properties (Danish names)
        nexus_client = manager.nexus_client
        borgere_client = manager.borgere
        organisationer_client = manager.organisationer
        opgaver_client = manager.opgaver
        indsats_client = manager.indsats
        kalender_client = manager.kalender
        forløb_client = manager.forløb
        
        # Verify all are the expected types
        assert isinstance(nexus_client, (NexusClient, Mock))
        assert isinstance(borgere_client, (BorgerClient, Mock))
        assert isinstance(organisationer_client, (OrganisationerClient, Mock))
        assert isinstance(opgaver_client, (OpgaverClient, Mock))
        assert isinstance(indsats_client, (IndsatsClient, Mock))
        assert isinstance(kalender_client, (KalenderClient, Mock))
        assert isinstance(forløb_client, (ForløbClient, Mock))
        
        # Verify lazy loading - accessing again should return same instances
        assert manager.nexus_client is nexus_client
        assert manager.borgere is borgere_client
        assert manager.organisationer is organisationer_client
        assert manager.opgaver is opgaver_client
        assert manager.indsats is indsats_client
        assert manager.kalender is kalender_client
        assert manager.forløb is forløb_client



class TestNexusClientManagerMethods:
    """Test methods added directly to NexusClientManager."""
    
    @patch('kmd_nexus_client.manager.NexusClient')
    def test_hent_fra_reference_method(self, mock_nexus_client):
        """Test that hent_fra_reference method works correctly."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Mock the underlying nexus client method
        mock_reference = {"_links": {"self": {"href": "test-url"}}}
        mock_resolved = {"id": "resolved-object", "name": "test"}
        
        mock_nexus_client_instance = Mock()
        mock_nexus_client_instance.hent_fra_reference.return_value = mock_resolved
        mock_nexus_client.return_value = mock_nexus_client_instance
        
        # Test the manager's hent_fra_reference method
        result = manager.hent_fra_reference(mock_reference)
        
        # Verify it called the underlying method correctly
        mock_nexus_client_instance.hent_fra_reference.assert_called_once_with(mock_reference)
        assert result == mock_resolved
        
    def test_hent_fra_reference_method_exists(self):
        """Test that hent_fra_reference method exists on manager."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id", 
            client_secret="test-client-secret"
        )
        
        assert hasattr(manager, 'hent_fra_reference')
        assert callable(manager.hent_fra_reference)