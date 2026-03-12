# Fixtures are automatically loaded from conftest.py
import os
from unittest.mock import Mock, patch

import pytest

from kmd_nexus_client.client import NexusClient


@patch("kmd_nexus_client.client.OAuth2Client")
def test_nexus_client_builds_urls_from_host(mock_oauth_client):
    mock_client = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {
        "_links": {"activeAssignments": {"href": "activeAssignments"}}
    }
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response
    mock_oauth_client.return_value = mock_client

    client = NexusClient(
        instance="unity",
        client_id="test-client-id",
        client_secret="test-client-secret",
        host="nexus-test",
    )

    assert (
        client.token_url
        == "https://iam.nexus-test.kmd.dk/authx/realms/unity/protocol/openid-connect/token"
    )
    assert client.base_url == "https://unity.nexus-test.kmd.dk/api/core/mobile/unity/v2/"
    assert (
        client.api["activeAssignments"]
        == "https://unity.nexus-test.kmd.dk/api/core/mobile/unity/v2/activeAssignments"
    )
    mock_client.fetch_token.assert_called_once_with()
    mock_client.get.assert_called_once_with(client.base_url)


def test_nexus_client_requires_host():
    with pytest.raises(ValueError, match="Host must be provided."):
        NexusClient(
            instance="unity",
            client_id="test-client-id",
            client_secret="test-client-secret",
            host=" ",
        )


def test_nexus_client_initialization(base_client):
    # Example test to verify initialization
    expected_host = os.getenv("HOST") or "nexus"

    assert base_client.base_url.startswith("https://")
    assert f".{expected_host}.kmd.dk" in base_client.base_url
    assert f"iam.{expected_host}.kmd.dk" in base_client.token_url

    assert base_client.api is not None
    assert "activeAssignments" in base_client.api
