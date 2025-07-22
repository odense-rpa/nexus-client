"""
KMD Nexus Python Klient

VIGTIGT: Brug altid NexusClientManager i stedet for individuelle klienter!

Anbefalet brug:
    from kmd_nexus_client import NexusClientManager
    
    nexus = NexusClientManager(instance="...", client_id="...", client_secret="...")
    borgere = nexus.borgere.hent_alle_borgere()
"""

from .client import NexusClient
from .manager import NexusClientManager
from .functionality.borgere import (
    BorgerClient,
    filter_pathway_references,
    filter_references,
)
from . import tree_helpers
from . import hooks

from .functionality.organisationer import OrganisationerClient
from .functionality.indsatser import IndsatsClient
from .functionality.opgaver import OpgaverClient
from .functionality.kalender import KalenderClient
from .functionality.forløb import ForløbClient

__all__ = [
    "NexusClient",
    "NexusClientManager",
    "BorgerClient",
    "filter_pathway_references",
    "filter_references",
    "OrganisationerClient",
    "IndsatsClient",
    "OpgaverClient",
    "KalenderClient",
    "ForløbClient",
    "tree_helpers",
    "hooks"
]
