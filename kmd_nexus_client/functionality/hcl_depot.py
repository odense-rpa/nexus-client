"""Reusable KMD Nexus HCL depot basket operations."""

from collections.abc import Mapping, Sequence
from time import monotonic, sleep
from typing import Any

from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.models import HclProductOrder, HclProductOrderResult


class HclDepotClient:
    """Client for HCL stock lookup and depot basket ordering."""

    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def order_product_for_patient(
        self,
        borger: Mapping[str, Any],
        order: HclProductOrder,
    ) -> HclProductOrderResult:
        """Place one HCL product order for a Nexus patient."""
        if order.amount < 1:
            return HclProductOrderResult.failed("Antal skal være mindst 1")

        basket = self._get_current_basket(borger)
        if basket is None:
            return HclProductOrderResult.failed("Borger har ingen depotkurv i Nexus")
        if basket.get("requests"):
            return HclProductOrderResult.failed(
                "Nexus depotkurv indeholder allerede åbne linjer"
            )

        depot = self._find_named_api_resource("hclDepots", order.depot_name)
        if depot is None:
            return HclProductOrderResult.failed(
                f"Nexus depot blev ikke fundet: {order.depot_name}"
            )

        product = self.find_product_by_hmi(
            order.hmi_number,
            depot_id=require_string(depot, "uid"),
            supplier_name=order.supplier_name,
        )
        if product is None:
            return HclProductOrderResult.failed(
                f"HMI {order.hmi_number} blev ikke fundet på {order.depot_name}"
            )

        item = self.find_available_product_item(
            product_id=require_string(product, "uid"),
            depot_id=require_string(depot, "uid"),
        )
        if item is None:
            return HclProductOrderResult.failed(
                f"HMI {order.hmi_number} er ikke på lager på {order.depot_name}"
            )

        grant = self.find_grant_for_order(
            borger,
            grant_name=order.grant_name,
            paragraph=order.grant_paragraph,
        )
        if grant is None:
            return HclProductOrderResult.failed(
                f"Nexus bevilling blev ikke fundet: {order.grant_name}"
            )

        request_id: str | None = None
        try:
            request_id = self._add_product_to_current_basket(
                borger=borger,
                product=product,
                product_item=item,
                depot=depot,
                grant=grant,
                amount=order.amount,
            )
            self._finalize_basket_order(
                borger=borger,
                request_id=request_id,
                grant_id=require_string(grant, "uid"),
                order=order,
            )
        except HTTPStatusError as exc:
            self._delete_request_if_present(borger, request_id)
            return HclProductOrderResult.failed(http_error_message(exc))
        except ValueError as exc:
            self._delete_request_if_present(borger, request_id)
            return HclProductOrderResult.failed(str(exc))

        refreshed_basket = self._get_current_basket(borger) or {}
        return HclProductOrderResult.success(
            basket_id=string_value(refreshed_basket.get("uid")),
            request_id=request_id,
        )

    def find_product_by_hmi(
        self,
        hmi_number: str,
        *,
        depot_id: str,
        supplier_name: str | None = None,
    ) -> Mapping[str, Any] | None:
        """Find an HCL product by exact HMI/catalog number and depot stock."""
        response = self.client.get(
            self.client.api["hclProductsByQuery"],
            params={"query": hmi_number},
        )
        products = response.json()
        if not isinstance(products, Sequence):
            return None

        matches = [
            product
            for product in products
            if isinstance(product, Mapping)
            and string_value(product.get("catalogIdentifier")) == hmi_number
            and supplier_matches(product, supplier_name)
        ]
        for product in matches:
            if product_has_depot_stock(product, depot_id):
                return product
        return matches[0] if matches else None

    def find_available_product_item(
        self,
        *,
        product_id: str,
        depot_id: str,
    ) -> Mapping[str, Any] | None:
        """Return an available stock item for a product at a depot."""
        response = self.client.get(
            self.client.api["hclProductItems"],
            params={"productId": product_id, "depotId": depot_id},
        )
        items = response.json()
        if not isinstance(items, Sequence):
            return None

        for item in items:
            if isinstance(item, Mapping) and is_available_product_item(item):
                return item
        return None

    def find_grant_for_order(
        self,
        borger: Mapping[str, Any],
        *,
        grant_name: str,
        paragraph: str,
    ) -> Mapping[str, Any] | None:
        """Find an active HCL grant matching the requested name and paragraph."""
        link = link_href(borger, "hclGrants")
        if link is None:
            return None

        grants = self.client.get(link).json()
        if not isinstance(grants, Sequence):
            return None

        for grant in grants:
            if not isinstance(grant, Mapping):
                continue
            if normalize_name(string_value(grant.get("status"))) != "active":
                continue
            if normalize_name(string_value(grant.get("name"))) != normalize_name(
                grant_name
            ):
                continue
            if normalize_name(string_value(grant.get("paragraph"))) != normalize_name(
                paragraph
            ):
                continue
            return grant
        return None

    def _get_current_basket(
        self, borger: Mapping[str, Any]
    ) -> Mapping[str, Any] | None:
        """Return the patient's current HCL basket details."""
        link = link_href(borger, "currentHclBasket")
        if link is None:
            return None
        basket = self.client.get(link).json()
        return basket if isinstance(basket, Mapping) else None

    def _get_current_basket_summary(
        self, borger: Mapping[str, Any]
    ) -> Mapping[str, Any] | None:
        """Return the patient's current HCL basket summary."""
        link = link_href(borger, "currentHclBasketSummary")
        if link is None:
            return None
        summary = self.client.get(link).json()
        return summary if isinstance(summary, Mapping) else None

    def _find_named_api_resource(
        self, api_key: str, name: str
    ) -> Mapping[str, Any] | None:
        """Find an active named resource from a Nexus index endpoint."""
        response = self.client.get(self.client.api[api_key])
        resources = response.json()
        if not isinstance(resources, Sequence):
            return None

        wanted = normalize_name(name)
        for resource in resources:
            if not isinstance(resource, Mapping):
                continue
            if resource.get("active") is False:
                continue
            if normalize_name(string_value(resource.get("name"))) == wanted:
                return resource
        return None

    def _add_product_to_current_basket(
        self,
        *,
        borger: Mapping[str, Any],
        product: Mapping[str, Any],
        product_item: Mapping[str, Any],
        depot: Mapping[str, Any],
        grant: Mapping[str, Any],
        amount: int,
    ) -> str:
        """Add a product item to the patient's current basket."""
        summary = self._get_current_basket_summary(borger)
        if summary is None:
            raise ValueError("Borger har ingen depotkurv-summary i Nexus")

        action = nested_mapping(summary, "actions", "addProductToCurrentBasket")
        if action is None:
            raise ValueError("Nexus depotkurv mangler addProductToCurrentBasket action")

        payload = dict(action)
        payload.update(
            {
                "patientId": require_patient_id(borger),
                "productId": require_string(product, "uid"),
                "productItemId": require_string(product_item, "uid"),
                "productItemNumber": product_item.get("itemNumber"),
                "depotId": require_string(depot, "uid"),
                "grantId": require_string(grant, "uid"),
                "onStock": True,
                "amount": amount,
                "amountConfirmed": True,
                "massItem": normalize_name(string_value(product.get("volumeType")))
                == "mass",
            }
        )

        actions_link = link_href(summary, "actions")
        if actions_link is None:
            raise ValueError("Nexus depotkurv mangler actions-link")

        before_ids = request_ids(self._get_current_basket(borger))
        self.client.post(actions_link, json=payload)
        after_ids = request_ids(self._get_current_basket(borger))
        new_ids = [
            request_id for request_id in after_ids if request_id not in before_ids
        ]
        if new_ids:
            return new_ids[0]
        if len(after_ids) == 1:
            return after_ids[0]
        raise ValueError("Kunne ikke finde ny depotkurv-linje i Nexus")

    def _finalize_basket_order(
        self,
        *,
        borger: Mapping[str, Any],
        request_id: str,
        grant_id: str,
        order: HclProductOrder,
    ) -> None:
        """Update delivery fields and finalize the basket."""
        delivery_type = self._find_named_api_resource(
            "hclDeliveryTypes", order.delivery_type_name
        )
        if delivery_type is None:
            raise ValueError(
                f"Kørselstype blev ikke fundet: {order.delivery_type_name}"
            )

        driving_zone = self._find_named_api_resource(
            "hclDrivingZones", order.driving_zone_name
        )
        if driving_zone is None:
            raise ValueError(f"Kørselszone blev ikke fundet: {order.driving_zone_name}")

        basket = self._get_current_basket(borger)
        if basket is None:
            raise ValueError("Borger har ingen depotkurv i Nexus")
        update_payload = self._build_basket_action_payload(
            basket=basket,
            action_name="update",
            request_id=request_id,
            grant_id=grant_id,
            order=order,
            delivery_type_id=require_string(delivery_type, "uid"),
            driving_zone_id=require_string(driving_zone, "uid"),
        )
        actions_link = link_href(basket, "actions")
        if actions_link is None:
            raise ValueError("Nexus depotkurv mangler actions-link")
        self.client.post(actions_link, json=update_payload)
        self._wait_until_request_is_ready(borger, request_id)

        basket = self._get_current_basket(borger)
        if basket is None:
            raise ValueError("Borger har ingen depotkurv i Nexus efter update")
        finalize_payload = self._build_basket_action_payload(
            basket=basket,
            action_name="finalize",
            request_id=request_id,
            grant_id=grant_id,
            order=order,
            delivery_type_id=require_string(delivery_type, "uid"),
            driving_zone_id=require_string(driving_zone, "uid"),
        )

        actions_link = link_href(basket, "actions")
        if actions_link is None:
            raise ValueError("Nexus depotkurv mangler actions-link")
        self.client.post(actions_link, json=finalize_payload)

    def _wait_until_request_is_ready(
        self,
        borger: Mapping[str, Any],
        request_id: str,
        *,
        timeout_seconds: float = 20.0,
        interval_seconds: float = 0.5,
    ) -> None:
        """Wait until Nexus has finished reserving/approving the basket request."""
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            basket = self._get_current_basket(borger)
            request = find_request(basket, request_id)
            if request is not None and request_is_ready(request):
                return
            sleep(interval_seconds)
        raise ValueError("Nexus depotkurv-linje blev ikke klar til bestilling")

    def _delete_request_if_present(
        self,
        borger: Mapping[str, Any],
        request_id: str | None,
    ) -> None:
        """Best-effort cleanup for failed basket operations."""
        if request_id is None:
            return

        basket = self._get_current_basket(borger)
        if basket is None:
            return

        action = nested_mapping(basket, "actions", "deleteRequest")
        actions_link = link_href(basket, "actions")
        if action is None or actions_link is None:
            return

        payload = dict(action)
        payload["requestId"] = request_id
        try:
            self.client.post(actions_link, json=payload)
        except HTTPStatusError:
            return

    def _build_basket_action_payload(
        self,
        *,
        basket: Mapping[str, Any],
        action_name: str,
        request_id: str,
        grant_id: str,
        order: HclProductOrder,
        delivery_type_id: str,
        driving_zone_id: str,
    ) -> dict[str, Any]:
        """Build the update/finalize basket action payload."""
        action = nested_mapping(basket, "actions", action_name)
        if action is None:
            raise ValueError(f"Nexus depotkurv mangler {action_name} action")

        payload = dict(action)
        payload["deliveryInformation"] = build_delivery_information(
            order=order,
            delivery_type_id=delivery_type_id,
            driving_zone_id=driving_zone_id,
        )
        payload["requestsInformation"] = [
            {
                "requestId": request_id,
                "buyStatus": None,
                "note": None,
                "grantId": grant_id,
                "plannedReturnDate": None,
            }
        ]
        return payload


def build_delivery_information(
    *,
    order: HclProductOrder,
    delivery_type_id: str,
    driving_zone_id: str,
) -> dict[str, Any]:
    """Build Nexus HCL delivery information from a product order."""
    address = order.delivery_address
    return {
        "handoverType": "DELIVERY",
        "requestedDeliveryDate": order.delivery_date.isoformat(),
        "deliveryTime": "NOT_SPECIFIED",
        "deliveryAddress": {
            "addressType": address.address_type,
            "deliveryAddress": address.delivery_address,
            "zipCode": address.zip_code,
            "city": address.city,
        },
        "phones": {
            "home": None,
            "work": None,
            "mobile": None,
            "other": order.phone_number,
        },
        "noteToDepot": order.note_to_depot,
        "deliveryTypeId": delivery_type_id,
        "deliveryZoneId": driving_zone_id,
    }


def product_has_depot_stock(product: Mapping[str, Any], depot_id: str) -> bool:
    """Return whether a product advertises available stock at the depot."""
    statistics = product.get("productItemStatistics")
    if not isinstance(statistics, Sequence):
        return False

    for statistic in statistics:
        if not isinstance(statistic, Mapping):
            continue
        if string_value(statistic.get("depotId")) != depot_id:
            continue
        for key in ("availableProductItems", "availableItems", "onStock"):
            value = statistic.get(key)
            if isinstance(value, int) and value > 0:
                return True
        if statistic.get("onStock") is True:
            return True
    return False


def is_available_product_item(item: Mapping[str, Any]) -> bool:
    """Return whether a product item looks available for ordering."""
    status = normalize_name(string_value(item.get("status")))
    if status and status not in {"available", "på lager", "paa lager"}:
        return False

    for key in ("availableAmount", "available", "onStock"):
        value = item.get(key)
        if isinstance(value, int) and value > 0:
            return True
        if value is True:
            return True

    item_number = item.get("itemNumber")
    return string_value(item.get("uid")) is not None and item_number is not None


def supplier_matches(product: Mapping[str, Any], supplier_name: str | None) -> bool:
    """Return whether a product supplier matches when a supplier was requested."""
    if supplier_name is None:
        return True
    return normalize_name(string_value(product.get("supplierName"))) == normalize_name(
        supplier_name
    )


def request_ids(basket: Mapping[str, Any] | None) -> list[str]:
    """Return request ids from basket details."""
    if basket is None:
        return []
    requests = basket.get("requests")
    if not isinstance(requests, Sequence):
        return []

    ids: list[str] = []
    for request in requests:
        if not isinstance(request, Mapping):
            continue
        request_id = string_value(request.get("uid") or request.get("id"))
        if request_id is not None:
            ids.append(request_id)
    return ids


def find_request(
    basket: Mapping[str, Any] | None, request_id: str
) -> Mapping[str, Any] | None:
    """Return a request from basket details by id."""
    if basket is None:
        return None
    requests = basket.get("requests")
    if not isinstance(requests, Sequence):
        return None

    for request in requests:
        if not isinstance(request, Mapping):
            continue
        if string_value(request.get("uid") or request.get("id")) == request_id:
            return request
    return None


def request_is_ready(request: Mapping[str, Any]) -> bool:
    """Return whether a basket request is ready for finalize."""
    reservation = request.get("reservation")
    if isinstance(reservation, Mapping) and reservation.get("pending") is True:
        return False

    status_values = [
        string_value(request.get("status")),
        string_value(request.get("approvalStatus")),
    ]
    return not any("pending" in normalize_name(value) for value in status_values)


def http_error_message(exc: HTTPStatusError) -> str:
    """Return a readable Nexus HTTP error message."""
    response = exc.response
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, Mapping):
        message = string_value(payload.get("message"))
        reason = string_value(payload.get("reason"))
        if message and reason and message != reason:
            return f"Nexus depotbestilling fejlede: {message} ({reason})"
        if message:
            return f"Nexus depotbestilling fejlede: {message}"

    return f"Nexus depotbestilling fejlede med HTTP {response.status_code}"


def require_patient_id(borger: Mapping[str, Any]) -> int:
    """Return the numeric Nexus patient id required by HCL basket actions."""
    patient_id = borger.get("id")
    if isinstance(patient_id, int):
        return patient_id
    raise ValueError("Nexus borger mangler numerisk id")


def require_string(payload: Mapping[str, Any], key: str) -> str:
    """Return a required string field from a Nexus payload."""
    value = string_value(payload.get(key))
    if value is None:
        raise ValueError(f"Nexus payload mangler {key}")
    return value


def link_href(payload: Mapping[str, Any], rel: str) -> str | None:
    """Return a HATEOAS link href from a Nexus payload."""
    links = payload.get("_links")
    if not isinstance(links, Mapping):
        return None
    link = links.get(rel)
    if not isinstance(link, Mapping):
        return None
    return string_value(link.get("href"))


def nested_mapping(payload: Mapping[str, Any], *keys: str) -> Mapping[str, Any] | None:
    """Return a nested mapping when every key exists with mapping values."""
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current if isinstance(current, Mapping) else None


def string_value(value: Any) -> str | None:
    """Return a stripped string value."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def normalize_name(value: str | None) -> str:
    """Normalize Nexus labels for stable comparisons."""
    if value is None:
        return ""
    return " ".join(value.casefold().split())
