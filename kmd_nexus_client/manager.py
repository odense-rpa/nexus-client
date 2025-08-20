"""
NexusClientManager - A facade/factory for all Nexus functionality clients.

This manager simplifies the instantiation of multiple clients by providing
a single entry point with lazy-loaded properties for each functionality.
"""

from typing import Optional
from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.borgere import BorgerClient
from kmd_nexus_client.functionality.organisationer import OrganisationerClient
from kmd_nexus_client.functionality.opgaver import OpgaverClient
from kmd_nexus_client.functionality.indsatser import IndsatsClient
from kmd_nexus_client.functionality.kalender import KalenderClient
from kmd_nexus_client.functionality.forløb import ForløbClient
from kmd_nexus_client.functionality.medcom import MedComClient


class NexusClientManager:
    """
    Manager til nem adgang til alle Nexus funktionalitets-klienter.

    VIGTIGT: Brug altid denne manager i stedet for at oprette individuelle klienter.
    Dette sikrer korrekt konfiguration og lazy loading.

    Eksempel:
        nexus = NexusClientManager(instance="...", client_id="...", client_secret="...")
        borger = nexus.borgere.hent_borger("1234567890")
        indsatser = nexus.indsatser.hent_indsatser_referencer(borger)
    """

    def __init__(
        self, instance: str, client_id: str, client_secret: str, timeout: float = 30.0
    ):
        """
        Initialize the NexusClientManager.

        Args:
            instance: The name of the Nexus instance
            client_id: The OAuth2 client ID
            client_secret: The OAuth2 client secret
            timeout: Request timeout in seconds (default: 30.0)
        """
        self._instance = instance
        self._client_id = client_id
        self._client_secret = client_secret

        # Store configuration for lazy loading
        self._config = {"timeout": timeout}

        # Lazy-loaded clients
        self._nexus_client: Optional[NexusClient] = None
        self._borgere_client: Optional["BorgerClient"] = None
        self._organisationer_client: Optional[OrganisationerClient] = None
        self._opgaver_client: Optional[OpgaverClient] = None
        self._indsats_client: Optional[IndsatsClient] = None
        self._kalender_client: Optional[KalenderClient] = None
        self._forløb_client: Optional[ForløbClient] = None
        self._medcom_client: Optional[MedComClient] = None

    @property
    def nexus_client(self) -> NexusClient:
        """Get the base NexusClient (lazy-loaded with configuration)."""
        if self._nexus_client is None:
            self._nexus_client = NexusClient(
                instance=self._instance,
                client_id=self._client_id,
                client_secret=self._client_secret,
                **self._config,
            )
        return self._nexus_client

    @property
    def borgere(self) -> "BorgerClient":
        """Get the BorgerClient (lazy-loaded)."""
        if self._borgere_client is None:
            self._borgere_client = BorgerClient(self.nexus_client)
        return self._borgere_client

    @property
    def organisationer(self) -> OrganisationerClient:
        """Get the OrganisationerClient (lazy-loaded)."""
        if self._organisationer_client is None:
            self._organisationer_client = OrganisationerClient(self.nexus_client)
        return self._organisationer_client

    @property
    def opgaver(self) -> OpgaverClient:
        """Get the OpgaverClient (lazy-loaded)."""
        if self._opgaver_client is None:
            self._opgaver_client = OpgaverClient(self.nexus_client)
        return self._opgaver_client

    @property
    def indsatser(self) -> IndsatsClient:
        """Get the IndsatsClient (lazy-loaded)."""
        if self._indsats_client is None:
            self._indsats_client = IndsatsClient(self.nexus_client)
        return self._indsats_client

    @property
    def kalender(self) -> KalenderClient:
        """Get the KalenderClient (lazy-loaded)."""
        if self._kalender_client is None:
            self._kalender_client = KalenderClient(self.nexus_client)
        return self._kalender_client

    @property
    def forløb(self) -> ForløbClient:
        """Get the ForløbClient (lazy-loaded)."""
        if self._forløb_client is None:
            self._forløb_client = ForløbClient(self.nexus_client)
        return self._forløb_client
    
    @property
    def medcom(self) -> MedComClient:
        """Get the MedComClient (lazy-loaded)."""
        if self._medcom_client is None:
            self._medcom_client = MedComClient(self.nexus_client)
        return self._medcom_client

    def hent_fra_reference(self, reference: dict) -> dict:
        """
        Hent fuldt objekt fra en reference.

        Convenience method for resolving references without having to drill down
        to the nexus_client. This provides a cleaner API for the common operation
        of resolving references.

        Args:
            reference: Referencen der skal følges til objektet.

        Returns:
            Det fulde objekt.

        Raises:
            ValueError: Hvis referencen ikke kan opløses.
        """
        return self.nexus_client.hent_fra_reference(reference)
