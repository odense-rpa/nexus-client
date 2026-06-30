"""
KMD Nexus Python Klient

VIGTIGT: Brug altid NexusClientManager i stedet for individuelle klienter!

Anbefalet brug:
    from kmd_nexus_client import NexusClientManager

    nexus = NexusClientManager(
        instance="...",
        client_id="...",
        client_secret="...",
        host="nexus",
    )
    borgere = nexus.borgere.hent_alle_borgere()
"""

from .client import NexusClient
from .manager import NexusClientManager
from .models import (
    HclDeliveryAddress,
    HclProductOrder,
    HclProductOrderResult,
    NexusBorger,
)
from . import tree_helpers
from . import hooks

from .functionality.borgere import BorgerClient
from .functionality.organisationer import OrganisationerClient
from .functionality.indsatser import IndsatsClient
from .functionality.opgaver import OpgaverClient
from .functionality.kalender import KalenderClient
from .functionality.forloeb import ForløbClient
from .functionality.hcl_depot import HclDepotClient

__all__ = [
    "NexusClientManager",
    "NexusClient",
    "HclDeliveryAddress",
    "HclProductOrder",
    "HclProductOrderResult",
    "NexusBorger",
    "BorgerClient",
    "HclDepotClient",
    "OrganisationerClient",
    "IndsatsClient",
    "OpgaverClient",
    "KalenderClient",
    "ForløbClient",
    "tree_helpers",
    "hooks",
]
