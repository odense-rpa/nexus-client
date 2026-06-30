"""Small stable values used by higher-level Nexus operations."""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class NexusBorger:
    """Minimal Nexus citizen data used by robot workflows."""

    citizen_id: str | None
    display_name: str | None
    cpr: str


@dataclass(frozen=True)
class OrganisationRelationEnsureResult:
    """Result of ensuring a citizen organisation relation."""

    created: bool
    relation: dict[str, Any]
    organisation: dict[str, Any]


@dataclass(frozen=True)
class PathwayEnsureResult:
    """Result of ensuring a Nexus pathway/case relation."""

    created: bool
    base_case: dict[str, Any] | None
    case: dict[str, Any] | None


@dataclass(frozen=True)
class HclDeliveryAddress:
    """Delivery address fields required by Nexus HCL depot basket actions."""

    delivery_address: str
    zip_code: str
    city: str
    address_type: str = "OTHER"


@dataclass(frozen=True)
class HclProductOrder:
    """Reusable Nexus HCL product order command."""

    hmi_number: str
    delivery_date: date
    delivery_address: HclDeliveryAddress
    supplier_name: str | None = None
    amount: int = 1
    depot_name: str = "Bornholm Depot"
    delivery_type_name: str = "Akut"
    driving_zone_name: str = "Bornholm"
    grant_name: str = "APV"
    grant_paragraph: str = "APV Udlån"
    phone_number: str | None = None
    note_to_depot: str | None = None


@dataclass(frozen=True)
class HclProductOrderResult:
    """Result returned by a Nexus HCL depot product order operation."""

    created: bool
    message: str
    basket_id: str | None = None
    request_id: str | None = None
    order_id: str | None = None
    lending_id: str | None = None

    @classmethod
    def success(
        cls,
        message: str = "Depotbestilling oprettet i Nexus",
        *,
        basket_id: str | None = None,
        request_id: str | None = None,
        order_id: str | None = None,
        lending_id: str | None = None,
    ) -> "HclProductOrderResult":
        """Return a successful depot product order result."""
        return cls(
            created=True,
            message=message,
            basket_id=basket_id,
            request_id=request_id,
            order_id=order_id,
            lending_id=lending_id,
        )

    @classmethod
    def failed(cls, message: str) -> "HclProductOrderResult":
        """Return a failed depot product order result."""
        return cls(created=False, message=message)
