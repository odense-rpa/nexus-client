from datetime import date
from typing import Any

import httpx

from kmd_nexus_client.functionality.hcl_depot import HclDepotClient
from kmd_nexus_client.models import HclDeliveryAddress, HclProductOrder


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeNexusClient:
    api = {
        "hclDepots": "depots",
        "hclProductsByQuery": "products",
        "hclProductItems": "items",
        "hclDeliveryTypes": "delivery-types",
        "hclDrivingZones": "driving-zones",
        "hclOrders": "hcl-orders",
    }

    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any]]] = []
        self.deletes: list[str] = []
        self.order: dict[str, Any] | None = None
        self.lendings: list[dict[str, Any]] = []
        self.basket = {
            "uid": "basket-1",
            "requests": [],
            "_links": {"actions": {"href": "basket-actions"}},
            "actions": {
                "update": {"type": "update", "basketId": "basket-1", "version": 1},
                "finalize": {
                    "type": "finalize",
                    "basketId": "basket-1",
                    "version": 2,
                    "orderedDate": None,
                },
                "deleteRequest": {
                    "type": "deleteRequest",
                    "basketId": "basket-1",
                    "requestId": None,
                },
            },
        }

    def get(self, endpoint: str, **kwargs: Any) -> FakeResponse:
        match endpoint:
            case "basket":
                return FakeResponse(self.basket)
            case "lendings":
                assert kwargs["params"] == {"active": "true"}
                return FakeResponse(self.lendings)
            case "lending-detail":
                return FakeResponse(
                    {
                        "uid": "lending-1",
                        "item": {"product": {"hmi": "84517"}},
                        "_links": {"orders": {"href": "lending-orders"}},
                    }
                )
            case "lending-orders":
                return FakeResponse([{"uid": "order-1"}] if self.order else [])
            case "hcl-orders":
                assert kwargs["params"] == {
                    "uid": "order-1",
                    "projection": "details",
                }
                return FakeResponse([self.order] if self.order else [])
            case "basket-summary":
                return FakeResponse(
                    {
                        "uid": "basket-1",
                        "_links": {"actions": {"href": "summary-actions"}},
                        "actions": {
                            "addProductToCurrentBasket": {
                                "type": "addProductToCurrentBasket",
                                "createdDate": None,
                            }
                        },
                    }
                )
            case "depots":
                return FakeResponse(
                    [{"uid": "depot-1", "name": "Bornholm Depot", "active": True}]
                )
            case "products":
                assert kwargs["params"] == {"query": "84517"}
                return FakeResponse(
                    [
                        {
                            "uid": "product-1",
                            "catalogIdentifier": "84517",
                            "supplierName": "Danish CARE Supply A/S",
                            "volumeType": "MASS",
                            "productItemStatistics": [
                                {
                                    "depotId": "depot-1",
                                    "availableProductItems": 4,
                                }
                            ],
                        }
                    ]
                )
            case "items":
                assert kwargs["params"] == {
                    "productId": "product-1",
                    "depotId": "depot-1",
                }
                return FakeResponse(
                    [{"uid": "item-1", "itemNumber": 7, "status": "AVAILABLE"}]
                )
            case "grants":
                return FakeResponse(
                    [
                        {
                            "uid": "grant-1",
                            "name": "APV",
                            "paragraph": "APV Udlån",
                            "status": "ACTIVE",
                        }
                    ]
                )
            case "delivery-types":
                return FakeResponse([{"uid": "delivery-1", "name": "Akut"}])
            case "driving-zones":
                return FakeResponse([{"uid": "zone-1", "name": "Bornholm"}])
            case _:
                raise AssertionError(f"Unexpected GET {endpoint}")

    def post(self, endpoint: str, json: dict[str, Any]) -> FakeResponse:
        self.posts.append((endpoint, json))
        if endpoint == "summary-actions":
            self.basket["requests"] = [{"uid": "request-1"}]
        if json.get("type") == "finalize":
            self.basket["requests"] = []
            self.order = {
                "uid": "order-1",
                "orderNumber": "00015801",
                "requests": [
                    {
                        "uid": "request-1",
                        "lendingId": "lending-1",
                        "product": {"catalogProductIdentifier": "84517"},
                        "_links": {"delete": {"href": "delete-request-1"}},
                    }
                ],
            }
            self.lendings = [
                {
                    "uid": "lending-1",
                    "item": {"catalogIdentifier": "84517"},
                    "_links": {"orders": {"href": "lending-orders"}},
                }
            ]
        return FakeResponse({})

    def delete(self, endpoint: str) -> FakeResponse:
        self.deletes.append(endpoint)
        if endpoint == "delete-request-1" and self.order is not None:
            self.order["requests"] = []
            self.lendings = []
        return FakeResponse({})


class FinalizeFailsNexusClient(FakeNexusClient):
    def post(self, endpoint: str, json: dict[str, Any]) -> FakeResponse:
        self.posts.append((endpoint, json))
        if endpoint == "summary-actions":
            self.basket["requests"] = [{"uid": "request-1"}]
            return FakeResponse({})
        if json["type"] == "finalize":
            request = httpx.Request("POST", "https://example.invalid/basket-actions")
            response = httpx.Response(
                400,
                json={"message": "REQUEST_IS_PENDING", "reason": "REQUEST_IS_PENDING"},
                request=request,
            )
            raise httpx.HTTPStatusError(
                "Finalize failed", request=request, response=response
            )
        if json["type"] == "deleteRequest":
            self.basket["requests"] = []
        return FakeResponse({})


class OptimisticLockOnceNexusClient(FakeNexusClient):
    def __init__(self) -> None:
        super().__init__()
        self.raised_optimistic_lock = False

    def post(self, endpoint: str, json: dict[str, Any]) -> FakeResponse:
        if (
            endpoint == "basket-actions"
            and json.get("type") == "update"
            and not self.raised_optimistic_lock
        ):
            self.raised_optimistic_lock = True
            self.posts.append((endpoint, json))
            request = httpx.Request("POST", "https://example.invalid/basket-actions")
            response = httpx.Response(
                409,
                text="org.eclipse.persistence.exceptions.OptimisticLockException",
                request=request,
            )
            raise httpx.HTTPStatusError(
                "Optimistic lock", request=request, response=response
            )
        return super().post(endpoint, json)


def make_borger() -> dict[str, Any]:
    return {
        "id": 123,
        "_links": {
            "currentHclBasket": {"href": "basket"},
            "currentHclBasketSummary": {"href": "basket-summary"},
            "hclGrants": {"href": "grants"},
            "lendings": {"href": "lendings"},
        },
    }


def make_order() -> HclProductOrder:
    return HclProductOrder(
        hmi_number="84517",
        supplier_name="Danish CARE Supply A/S",
        delivery_date=date(2026, 5, 20),
        delivery_address=HclDeliveryAddress(
            delivery_address="Midlertidigvej 2",
            zip_code="3720",
            city="Aakirkeby",
        ),
        phone_number="56990000",
        note_to_depot="Bopælsadresse: Bopælsvej 1, 3700 Rønne. ATP",
    )


def make_order_without_phone() -> HclProductOrder:
    return HclProductOrder(
        hmi_number="84517",
        supplier_name="Danish CARE Supply A/S",
        delivery_date=date(2026, 5, 20),
        delivery_address=HclDeliveryAddress(
            delivery_address="Midlertidigvej 2",
            zip_code="3720",
            city="Aakirkeby",
        ),
        phone_number=None,
        note_to_depot="ATP",
    )


def test_order_product_for_patient_adds_updates_and_finalizes_basket() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)

    result = hcl.order_product_for_patient(make_borger(), make_order())

    assert result.created
    assert result.request_id == "request-1"
    assert result.order_id == "order-1"
    assert result.lending_id == "lending-1"
    assert [post[0] for post in client.posts] == [
        "summary-actions",
        "basket-actions",
        "basket-actions",
    ]
    add_payload = client.posts[0][1]
    assert add_payload["productId"] == "product-1"
    assert add_payload["productItemId"] == "item-1"
    assert add_payload["productItemNumber"] == 7
    assert add_payload["depotId"] == "depot-1"
    assert add_payload["grantId"] == "grant-1"
    assert add_payload["amount"] == 1
    assert add_payload["massItem"] is True

    update_payload = client.posts[1][1]
    assert update_payload["deliveryInformation"]["deliveryTypeId"] == "delivery-1"
    assert update_payload["deliveryInformation"]["deliveryZoneId"] == "zone-1"
    assert update_payload["deliveryInformation"]["deliveryAddress"] == {
        "addressType": "OTHER",
        "deliveryAddress": "Midlertidigvej 2",
        "zipCode": "3720",
        "city": "Aakirkeby",
    }
    assert update_payload["deliveryInformation"]["phones"]["other"] == "56990000"
    assert update_payload["requestsInformation"] == [
        {
            "requestId": "request-1",
            "buyStatus": None,
            "note": None,
            "grantId": "grant-1",
            "plannedReturnDate": None,
        }
    ]

    finalize_payload = client.posts[2][1]
    assert finalize_payload["type"] == "finalize"
    assert finalize_payload["orderedDate"] is None


def test_order_product_uses_patient_stamdata_phone_when_order_phone_is_missing() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)
    borger = {**make_borger(), "mobileTelephone": "12345678"}

    result = hcl.order_product_for_patient(borger, make_order_without_phone())

    assert result.created
    update_payload = client.posts[1][1]
    assert update_payload["deliveryInformation"]["phones"] == {
        "home": None,
        "work": None,
        "mobile": "12345678",
        "other": None,
    }


def test_order_product_fails_before_basket_mutation_when_phone_is_missing() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)

    result = hcl.order_product_for_patient(make_borger(), make_order_without_phone())

    assert not result.created
    assert result.message == "Nexus depotbestilling mangler telefonnummer"
    assert client.posts == []


def test_order_product_retries_once_on_optimistic_basket_lock() -> None:
    client = OptimisticLockOnceNexusClient()
    hcl = HclDepotClient(client)

    result = hcl.order_product_for_patient(make_borger(), make_order())

    assert result.created
    assert [post[1]["type"] for post in client.posts] == [
        "addProductToCurrentBasket",
        "update",
        "update",
        "finalize",
    ]


def test_order_product_returns_failure_when_basket_has_existing_lines() -> None:
    client = FakeNexusClient()
    client.basket["requests"] = [{"uid": "someone-elses-line"}]
    hcl = HclDepotClient(client)

    result = hcl.order_product_for_patient(make_borger(), make_order())

    assert not result.created
    assert result.message == "Nexus depotkurv indeholder allerede åbne linjer"
    assert client.posts == []


def test_order_product_returns_failure_when_product_is_not_on_stock() -> None:
    client = FakeNexusClient()
    original_get = client.get

    def get_without_items(endpoint: str, **kwargs: Any) -> FakeResponse:
        if endpoint == "items":
            return FakeResponse([])
        return original_get(endpoint, **kwargs)

    client.get = get_without_items  # type: ignore[method-assign]
    hcl = HclDepotClient(client)

    result = hcl.order_product_for_patient(make_borger(), make_order())

    assert not result.created
    assert result.message == "HMI 84517 er ikke på lager på Bornholm Depot"
    assert client.posts == []


def test_order_product_cleans_basket_when_finalize_fails() -> None:
    client = FinalizeFailsNexusClient()
    hcl = HclDepotClient(client)

    result = hcl.order_product_for_patient(make_borger(), make_order())

    assert not result.created
    assert result.message == "Nexus depotbestilling fejlede: REQUEST_IS_PENDING"
    assert client.basket["requests"] == []
    assert [post[1]["type"] for post in client.posts] == [
        "addProductToCurrentBasket",
        "update",
        "finalize",
        "deleteRequest",
    ]


def test_delete_order_request_removes_finalized_order_line() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)
    result = hcl.order_product_for_patient(make_borger(), make_order())

    deleted = hcl.delete_order_request(
        order_id=result.order_id or "",
        request_id=result.request_id or "",
    )

    assert deleted
    assert client.deletes == ["delete-request-1"]
    assert client.order is not None
    assert client.order["requests"] == []


def test_delete_order_request_is_idempotent_when_line_is_already_missing() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)
    result = hcl.order_product_for_patient(make_borger(), make_order())
    assert hcl.delete_order_request(
        order_id=result.order_id or "",
        request_id=result.request_id or "",
    )

    deleted_again = hcl.delete_order_request(
        order_id=result.order_id or "",
        request_id=result.request_id or "",
    )

    assert deleted_again
    assert client.deletes == ["delete-request-1"]


def test_delete_patient_order_requests_by_hmi_removes_matching_lines() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)
    hcl.order_product_for_patient(make_borger(), make_order())

    deleted = hcl.delete_patient_order_requests_by_hmi(
        make_borger(),
        hmi_number="84517",
    )

    assert deleted == 1
    assert client.deletes == ["delete-request-1"]
    assert client.order is not None
    assert client.order["requests"] == []


def test_delete_patient_order_requests_by_hmi_follows_detailed_lending_orders_link() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)
    hcl.order_product_for_patient(make_borger(), make_order())
    client.lendings = [
        {"uid": "lending-1", "_links": {"self": {"href": "lending-detail"}}}
    ]

    deleted = hcl.delete_patient_order_requests_by_hmi(
        make_borger(),
        hmi_number="84517",
    )

    assert deleted == 1
    assert client.deletes == ["delete-request-1"]


def test_delete_current_basket_requests_by_hmi_removes_matching_lines() -> None:
    client = FakeNexusClient()
    client.basket["requests"] = [
        {"uid": "request-1", "product": {"catalogProductIdentifier": "84517"}},
        {"uid": "request-2", "product": {"catalogProductIdentifier": "12345"}},
    ]
    hcl = HclDepotClient(client)

    deleted = hcl.delete_current_basket_requests_by_hmi(
        make_borger(),
        hmi_number="84517",
    )

    assert deleted == 1
    assert client.posts[-1][0] == "basket-actions"
    assert client.posts[-1][1]["type"] == "deleteRequest"
    assert client.posts[-1][1]["requestId"] == "request-1"
