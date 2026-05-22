from typing import Any

import httpx

from kmd_nexus_client.functionality.borgere import (
    BorgerClient,
    parse_nexus_patient_identifier,
)
from kmd_nexus_client.models import NexusBorger


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeNexusClient:
    api = {
        "patientDetailsSearch": "patient-details",
        "searchPatients": "search-patients",
    }

    def __init__(
        self,
        *,
        details_payload: Any | None = None,
        search_payload: Any | None = None,
        resolved_payloads: dict[str, Any] | None = None,
        details_status_code: int | None = None,
    ) -> None:
        self.details_payload = details_payload
        self.search_payload = search_payload or []
        self.resolved_payloads = resolved_payloads or {}
        self.details_status_code = details_status_code

    def post(self, endpoint: str, json: dict[str, Any]) -> FakeResponse:
        assert endpoint == "patient-details"
        assert json["keyType"] == "CPR"
        if self.details_status_code is not None:
            request = httpx.Request("POST", "https://example.invalid/patient-details")
            response = httpx.Response(self.details_status_code, request=request)
            raise httpx.HTTPStatusError(
                "Details lookup failed", request=request, response=response
            )
        return FakeResponse(self.details_payload)

    def get(self, endpoint: str, **kwargs: Any) -> FakeResponse:
        if endpoint in self.resolved_payloads:
            return FakeResponse(self.resolved_payloads[endpoint])
        assert endpoint == "search-patients"
        assert kwargs["params"]["maxResults"] == 10
        return FakeResponse(self.search_payload)


def test_find_borger_by_cpr_returns_stable_value_from_details_lookup() -> None:
    client = BorgerClient(
        FakeNexusClient(
            details_payload={
                "isPatientAccessible": True,
                "patient": {
                    "id": 12384,
                    "fullName": "Stig Moller",
                    "patientIdentifier": {"identifier": "131152-1105"},
                },
            }
        )
    )

    assert client.find_borger_by_cpr("1311521105") == NexusBorger(
        citizen_id="12384",
        display_name="Stig Moller",
        cpr="1311521105",
    )


def test_find_borger_by_cpr_uses_search_fallback_after_404() -> None:
    client = BorgerClient(
        FakeNexusClient(
            details_status_code=404,
            search_payload=[
                {
                    "id": 987,
                    "displayName": "Wrong Citizen",
                    "patientIdentifier": {"identifier": "0101019999"},
                },
                {
                    "id": 12384,
                    "displayName": "Stig Moller",
                    "patientIdentifier": {"identifier": "131152-1105"},
                },
            ],
        )
    )

    assert client.find_borger_by_cpr("131152-1105") == NexusBorger(
        citizen_id="12384",
        display_name="Stig Moller",
        cpr="1311521105",
    )


def test_hent_borger_uses_exact_anonymous_identifier_search_fallback() -> None:
    client = BorgerClient(
        FakeNexusClient(
            details_payload={"isPatientAccessible": False},
            search_payload=[
                {
                    "id": 12384,
                    "displayName": "Stig Moller",
                    "patientIdentifier": {
                        "type": "anonymous",
                        "identifier": "1311521105",
                    },
                    "_links": {"self": {"href": "patients/12384"}},
                }
            ],
            resolved_payloads={
                "patients/12384": {
                    "id": 12384,
                    "fullName": "Stig Moller",
                    "patientIdentifier": {
                        "type": "anonymous",
                        "identifier": "1311521105",
                    },
                    "_links": {
                        "patientOrganizations": {"href": "patient-organizations"}
                    },
                }
            },
        )
    )

    citizen = client.hent_borger("131152-1105")

    assert citizen is not None
    assert citizen["id"] == 12384
    assert citizen["fullName"] == "Stig Moller"
    assert "patientOrganizations" in citizen["_links"]


def test_find_borger_by_cpr_returns_none_when_citizen_is_inaccessible() -> None:
    client = BorgerClient(
        FakeNexusClient(details_payload={"isPatientAccessible": False})
    )

    assert client.find_borger_by_cpr("1311521105") is None


def test_parse_nexus_patient_identifier_accepts_string_and_nested_shapes() -> None:
    assert (
        parse_nexus_patient_identifier({"patientIdentifier": "131152-1105"})
        == "1311521105"
    )
    assert (
        parse_nexus_patient_identifier(
            {"patientIdentifier": {"identifier": "1311521105"}}
        )
        == "1311521105"
    )
