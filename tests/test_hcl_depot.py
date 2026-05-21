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
    }

    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any]]] = []
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


def make_borger() -> dict[str, Any]:
    return {
        "id": 123,
        "_links": {
            "currentHclBasket": {"href": "basket"},
            "currentHclBasketSummary": {"href": "basket-summary"},
            "hclGrants": {"href": "grants"},
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


def test_order_product_for_patient_adds_updates_and_finalizes_basket() -> None:
    client = FakeNexusClient()
    hcl = HclDepotClient(client)

    result = hcl.order_product_for_patient(make_borger(), make_order())

    assert result.created
    assert result.request_id == "request-1"
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
