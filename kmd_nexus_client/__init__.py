from .client import NexusClient
from .manager import NexusClientManager
from .functionality.borgere import (
    BorgerClient,
    CitizensClient,  # Backward compatibility
    filter_pathway_references,
    filter_references,
)
from . import tree_helpers
from . import hooks

from .functionality.organisationer import OrganisationerClient
from .functionality.indsatser import IndsatsClient, GrantsClient
from .functionality.opgaver import OpgaverClient, AssignmentsClient
from .functionality.kalender import KalenderClient, CalendarClient
from .functionality.forløb import ForløbClient, CasesClient

__all__ = [
    "NexusClient",
    "NexusClientManager",
    "BorgerClient",
    "CitizensClient",  # Backward compatibility
    "filter_pathway_references",
    "filter_references",
    "OrganisationerClient",
    "GrantsClient",  # Backward compatibility
    "IndsatsClient",
    "OpgaverClient",
    "AssignmentsClient",  # Backward compatibility
    "KalenderClient",
    "CalendarClient",  # Backward compatibility
    "ForløbClient",
    "CasesClient",  # Backward compatibility
    "tree_helpers",
    "hooks"
]
