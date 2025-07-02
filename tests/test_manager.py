"""
Tests for NexusClientManager functionality.
"""

import pytest
from unittest.mock import Mock, patch
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.borgere import BorgerClient
from kmd_nexus_client.functionality.organizations import OrganizationsClient
from kmd_nexus_client.functionality.assignments import AssignmentsClient
from kmd_nexus_client.functionality.grants import GrantsClient
from kmd_nexus_client.functionality.calendar import CalendarClient
from kmd_nexus_client.functionality.cases import CasesClient


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
        assert manager._enable_ai_safety is False
        
        # All clients should be None initially (lazy loading)
        assert manager._nexus_client is None
        assert manager._borgere_client is None
        assert manager._organizations_client is None
        assert manager._assignments_client is None
        assert manager._grants_client is None
        assert manager._calendar_client is None
        assert manager._cases_client is None
    
    def test_manager_initialization_with_ai_safety(self):
        """Test that the manager initializes correctly with AI safety enabled."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret",
            enable_ai_safety=True
        )
        
        assert manager._enable_ai_safety is True
    
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
        
        # Check that hook parameters are present (defaults)
        assert "enable_logging" in kwargs
        assert "enable_error_context" in kwargs
        
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
        
        # Access citizens property (backward compatibility)
        citizens = manager.citizens
        
        # Should be called now
        mock_borgere_client.assert_called_once()
        
        # Second access should return the same instance
        citizens2 = manager.citizens
        assert citizens is citizens2
        
        # BorgerClient constructor should still only be called once
        assert mock_borgere_client.call_count == 1
    
    @patch('kmd_nexus_client.manager.NexusClient')
    @patch('kmd_nexus_client.manager._SafeBorgerClient')
    def test_citizens_client_with_ai_safety(self, mock_safe_borgere_client, mock_nexus_client):
        """Test that the SafeBorgerClient is used when AI safety is enabled."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret",
            enable_ai_safety=True
        )
        
        # Access citizens property (backward compatibility)
        citizens = manager.citizens
        
        # Should use SafeBorgerClient instead of regular BorgerClient
        mock_safe_borgere_client.assert_called_once()
    
    @patch('kmd_nexus_client.manager.NexusClient')
    @patch('kmd_nexus_client.manager.CalendarClient')
    def test_calendar_client_dependencies(self, mock_calendar_client, mock_nexus_client):
        """Test that CalendarClient gets the correct dependencies."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Access calendar property
        calendar = manager.calendar
        
        # CalendarClient should be called with both nexus_client and citizens_client
        mock_calendar_client.assert_called_once()
        call_args = mock_calendar_client.call_args[0]
        
        # First argument should be the nexus client
        assert call_args[0] == manager.nexus_client
        # Second argument should be the citizens client
        assert call_args[1] == manager.borgere
    
    @patch('kmd_nexus_client.manager.NexusClient')
    def test_all_clients_lazy_loading(self, mock_nexus_client):
        """Test that all functionality clients are lazy-loaded."""
        manager = NexusClientManager(
            instance="test-instance",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        
        # Access all client properties
        nexus_client = manager.nexus_client
        citizens_client = manager.citizens
        organizations_client = manager.organizations
        assignments_client = manager.assignments
        grants_client = manager.grants
        calendar_client = manager.calendar
        cases_client = manager.cases
        
        # Verify all are the expected types
        assert isinstance(nexus_client, (NexusClient, Mock))
        assert isinstance(citizens_client, (BorgerClient, Mock))
        assert isinstance(organizations_client, (OrganizationsClient, Mock))
        assert isinstance(assignments_client, (AssignmentsClient, Mock))
        assert isinstance(grants_client, (GrantsClient, Mock))
        assert isinstance(calendar_client, (CalendarClient, Mock))
        assert isinstance(cases_client, (CasesClient, Mock))
        
        # Verify lazy loading - accessing again should return same instances
        assert manager.nexus_client is nexus_client
        assert manager.borgere is citizens_client  # borgere is the new primary property
        assert manager.citizens is citizens_client  # citizens is backward compat
        assert manager.organizations is organizations_client
        assert manager.assignments is assignments_client
        assert manager.grants is grants_client
        assert manager.calendar is calendar_client
        assert manager.cases is cases_client


class TestSafeBorgerClient:
    """Test the _SafeBorgerClient class."""
    
    @patch('kmd_nexus_client.nexus_ai_safety_wrapper.safe_get_citizen')
    def test_safe_hent_borger_with_wrapper(self, mock_safe_get_citizen):
        """Test that safe_get_citizen is used when available."""
        from kmd_nexus_client.manager import _SafeBorgerClient
        
        mock_nexus_client = Mock()
        safe_client = _SafeBorgerClient(mock_nexus_client)
        
        mock_safe_get_citizen.return_value = {"id": "test-citizen"}
        
        result = safe_client.hent_borger("1234567890")
        
        mock_safe_get_citizen.assert_called_once_with(safe_client, "1234567890")
        assert result == {"id": "test-citizen"}
    
    def test_safe_get_citizen_fallback(self):
        """Test that SafeBorgerClient can be instantiated and has fallback behavior."""
        from kmd_nexus_client.manager import _SafeBorgerClient
        
        mock_nexus_client = Mock()
        safe_client = _SafeBorgerClient(mock_nexus_client)
        
        # Test that it's an instance of BorgerClient (inheritance works)
        from kmd_nexus_client.functionality.borgere import BorgerClient
        assert isinstance(safe_client, BorgerClient)
        
        # Test that the hent_borger method exists and can be called
        assert hasattr(safe_client, 'hent_borger')
        assert callable(safe_client.hent_borger)
        
        # Test backward compatibility
        assert hasattr(safe_client, 'get_citizen')
        assert callable(safe_client.get_citizen)