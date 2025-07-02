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
from .functionality.assignments import AssignmentsClient
from .functionality.calendar import CalendarClient
from .functionality.cases import CasesClient

__all__ = [
    "NexusClient",
    "NexusClientManager",
    "BorgerClient",
    "CitizensClient",  # Backward compatibility
    "filter_pathway_references",
    "filter_references",
    "OrganizationsClient",
    "GrantsClient",
    "AssignmentsClient",
    "CalendarClient",
    "CasesClient",
    "tree_helpers",
    "hooks"
]
