"""
NexusClientManager - A facade/factory for all Nexus functionality clients.

This manager simplifies the instantiation of multiple clients by providing
a single entry point with lazy-loaded properties for each functionality.
"""

from typing import Optional, Dict, List, Callable
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.borgere import BorgerClient
from kmd_nexus_client.functionality.organizations import OrganizationsClient
from kmd_nexus_client.functionality.assignments import AssignmentsClient
from kmd_nexus_client.functionality.grants import GrantsClient
from kmd_nexus_client.functionality.calendar import CalendarClient
from kmd_nexus_client.functionality.cases import CasesClient


class NexusClientManager:
    """
    A manager class that provides simplified access to all Nexus functionality clients.
    
    This class acts as a facade that automatically handles the instantiation and
    dependencies of all functionality clients, reducing the boilerplate code
    needed when working with the Nexus API.
    
    Example:
        >>> nexus = NexusClientManager(
        ...     instance="your-instance",
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret"
        ... )
        >>> citizen = nexus.citizens.get_citizen("1234567890")
        >>> events = nexus.calendar.events(calendar, start_date, end_date)
    """
    
    def __init__(
        self,
        instance: str,
        client_id: str,
        client_secret: str,
        enable_ai_safety: bool = False,
        enable_logging: bool = True,
        non_logging_endpoints: Optional[List[str]] = None,
        enable_error_context: bool = True,
        enable_timing: bool = False,
        enable_metrics: bool = False,
        custom_hooks: Optional[Dict[str, List[Callable]]] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the NexusClientManager.
        
        Args:
            instance: The name of the Nexus instance
            client_id: The OAuth2 client ID
            client_secret: The OAuth2 client secret
            enable_ai_safety: Whether to enable AI safety wrapper integration
            enable_logging: Enable request/response logging (default: True)
            non_logging_endpoints: List of endpoint suffixes to skip logging
            enable_error_context: Enable enhanced error context (default: True)
            enable_timing: Enable request timing tracking (default: False)
            enable_metrics: Enable basic metrics collection (default: False)
            custom_hooks: Custom HTTPX event hooks to add
            timeout: Request timeout in seconds (default: 30.0)
        """
        self._instance = instance
        self._client_id = client_id
        self._client_secret = client_secret
        self._enable_ai_safety = enable_ai_safety
        
        # Store hook configuration for lazy loading
        self._hook_config = {
            'enable_logging': enable_logging,
            'non_logging_endpoints': non_logging_endpoints,
            'enable_error_context': enable_error_context,
            'enable_timing': enable_timing,
            'enable_metrics': enable_metrics,
            'custom_hooks': custom_hooks,
            'timeout': timeout
        }
        
        # Lazy-loaded clients
        self._nexus_client: Optional[NexusClient] = None
        self._borgere_client: Optional["BorgerClient"] = None
        self._organizations_client: Optional[OrganizationsClient] = None
        self._assignments_client: Optional[AssignmentsClient] = None
        self._grants_client: Optional[GrantsClient] = None
        self._calendar_client: Optional[CalendarClient] = None
        self._cases_client: Optional[CasesClient] = None
    
    @property
    def nexus_client(self) -> NexusClient:
        """Get the base NexusClient (lazy-loaded with hook configuration)."""
        if self._nexus_client is None:
            self._nexus_client = NexusClient(
                instance=self._instance,
                client_id=self._client_id,
                client_secret=self._client_secret,
                **self._hook_config
            )
        return self._nexus_client
    
    @property
    def borgere(self) -> "BorgerClient":
        """Get the BorgerClient (lazy-loaded)."""
        if self._borgere_client is None:
            if self._enable_ai_safety:
                # Create a safety-wrapped version
                self._borgere_client = _SafeBorgerClient(self.nexus_client)
            else:
                self._borgere_client = BorgerClient(self.nexus_client)
        return self._borgere_client
    
    @property
    def organizations(self) -> OrganizationsClient:
        """Get the OrganizationsClient (lazy-loaded)."""
        if self._organizations_client is None:
            self._organizations_client = OrganizationsClient(self.nexus_client)
        return self._organizations_client
    
    @property
    def assignments(self) -> AssignmentsClient:
        """Get the AssignmentsClient (lazy-loaded)."""
        if self._assignments_client is None:
            self._assignments_client = AssignmentsClient(self.nexus_client)
        return self._assignments_client
    
    @property
    def grants(self) -> GrantsClient:
        """Get the GrantsClient (lazy-loaded)."""
        if self._grants_client is None:
            self._grants_client = GrantsClient(self.nexus_client)
        return self._grants_client
    
    @property
    def calendar(self) -> CalendarClient:
        """Get the CalendarClient (lazy-loaded with automatic BorgerClient dependency)."""
        if self._calendar_client is None:
            self._calendar_client = CalendarClient(self.nexus_client, self.borgere)
        return self._calendar_client
    
    # Backward compatibility property
    @property
    def citizens(self):
        """DEPRECATED: Use borgere property instead."""
        return self.borgere
    
    @property
    def cases(self) -> CasesClient:
        """Get the CasesClient (lazy-loaded)."""
        if self._cases_client is None:
            self._cases_client = CasesClient(self.nexus_client)
        return self._cases_client


class _SafeBorgerClient(BorgerClient):
    """
    A safety-wrapped version of CitizensClient that integrates with the AI safety wrapper.
    
    This class overrides the get_citizen method to use the safe_get_citizen function
    from the nexus_ai_safety_wrapper module.
    """
    
    def hent_borger(self, borger_cpr: str) -> dict:
        """
        Hent en borger via CPR nummer med AI safety wrapper.
        
        Denne metode bruger safe_get_citizen funktionen som automatisk
        validerer at CPR'et er en af de godkendte test-borgere.
        
        Args:
            borger_cpr: CPR nummeret på borgeren der skal hentes
            
        Returns:
            Borgerens detaljer, eller None hvis borgeren ikke blev fundet
            
        Raises:
            NexusSecurityError: Hvis CPR'et ikke er en godkendt test-borger
        """
        try:
            from kmd_nexus_client.nexus_ai_safety_wrapper import safe_get_citizen
            return safe_get_citizen(self, borger_cpr)
        except ImportError:
            # Fall back to regular implementation if safety wrapper is not available
            return super().hent_borger(borger_cpr)
    
    # Backward compatibility for safety wrapper
    def get_citizen(self, citizen_cpr: str) -> dict:
        """DEPRECATED: Use hent_borger() instead."""
        return self.hent_borger(citizen_cpr)