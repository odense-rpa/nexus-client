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

from .functionality.organizations import OrganizationsClient
from .functionality.grants import GrantsClient
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
    "OrganizationsClient",
    "GrantsClient",
    "OpgaverClient",
    "AssignmentsClient",  # Backward compatibility
    "KalenderClient",
    "CalendarClient",  # Backward compatibility
    "ForløbClient",
    "CasesClient",  # Backward compatibility
    "tree_helpers",
    "hooks"
]
