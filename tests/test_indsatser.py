import pytest

# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.functionality.indsatser import IndsatsClient


def test_hent_indsats_elementer(nexus_manager: NexusClientManager, test_indsats: dict):
    """Test hent_indsats_elementer Danish function."""
    elementer = nexus_manager.indsatser.hent_indsats_elementer(test_indsats)

    assert elementer is not None


def test_indsats_client_methods_exist(nexus_manager: NexusClientManager):
    """Test that all Danish methods exist on IndsatsClient."""
    # Check that all methods exist
    assert hasattr(nexus_manager.indsatser, "rediger_indsats")
    assert hasattr(nexus_manager.indsatser, "hent_indsats_elementer")
    assert hasattr(nexus_manager.indsatser, "opret_indsats")
    assert hasattr(nexus_manager.indsatser, "hent_indsats")
    assert hasattr(nexus_manager.indsatser, "hent_indsats_ved_id")
    assert hasattr(nexus_manager.indsatser, "annuller_indsats")
    assert hasattr(nexus_manager.indsatser, "filtrer_indsats_referencer")

    # Check that they are callable
    assert callable(nexus_manager.indsatser.rediger_indsats)
    assert callable(nexus_manager.indsatser.hent_indsats_elementer)
    assert callable(nexus_manager.indsatser.opret_indsats)
    assert callable(nexus_manager.indsatser.hent_indsats)
    assert callable(nexus_manager.indsatser.hent_indsats_ved_id)
    assert callable(nexus_manager.indsatser.annuller_indsats)
    assert callable(nexus_manager.indsatser.filtrer_indsats_referencer)


def test_filtrer_indsats_referencer_empty_list(nexus_manager: NexusClientManager):
    """Test filtrer_indsats_referenser with empty input."""
    # Test filtering empty list
    filtered = nexus_manager.indsatser.filtrer_indsats_referencer(
        [], kun_aktive=True, leverandør_navn=""
    )

    assert filtered == []


def test_filtrer_indsats_referencer_real_data(
    nexus_manager: NexusClientManager, test_borger: dict
):
    visning = nexus_manager.borgere.hent_visning(test_borger)
    assert visning is not None, "Visning should not be None"

    referencer = nexus_manager.borgere.hent_referencer(visning)
    assert referencer is not None, "Referencer should not be None"

    alle_indsatser = nexus_manager.indsatser.filtrer_indsats_referencer(
        referencer, kun_aktive=False
    )
    assert len(alle_indsatser) > 0, "Der skal være referencer"

    aktive_indsatser = nexus_manager.indsatser.filtrer_indsats_referencer(
        referencer, kun_aktive=True
    )
    assert len(aktive_indsatser) > 0, "Der skal være aktive referencer"
    assert len(alle_indsatser) >= len(aktive_indsatser), (
        "Aktive referencer skal være en del af alle referencer"
    )

    leverandør_indsatser = nexus_manager.indsatser.filtrer_indsats_referencer(
        referencer, kun_aktive=False, leverandør_navn="Testleverandør Supporten Dag"
    )
    assert len(leverandør_indsatser) > 0, "Der skal være leverandør referencer"
    assert len(leverandør_indsatser) <= len(aktive_indsatser), (
        "Leverandør referencer skal være en del af alle referencer"
    )

    for indsats in leverandør_indsatser:
        leverandør = next(
            (
                info
                for info in indsats.get("additionalInfo", [])
                if info.get("key") == "Leverandør"
                and info.get("value") == "Testleverandør Supporten Dag"
            ),
            None,
        )

        assert leverandør is not None, "Leverandør skal findes i additionalInfo"


def test_filtrer_indsats_referencer_with_mock_data(nexus_manager: NexusClientManager):
    """Test filtrer_indsats_referencer with mock data."""
    # Create mock grant references
    mock_referenser = [
        {
            "type": "basketGrantReference",
            "workflowState": {"name": "Bestilt"},
            "additionalInfo": [],
        },
        {
            "type": "basketGrantReference",
            "workflowState": {"name": "Afsluttet"},
            "additionalInfo": [],
        },
        {
            "type": "basketGrantReference",
            "workflowState": {"name": "Bevilliget"},
            "additionalInfo": [
                {"key": "Something"},
                {"key": "Else"},
                {"key": "Leverandør", "value": "Test Leverandør"},
            ],
        },
    ]

    # Test filtering for active only
    aktive = nexus_manager.indsatser.filtrer_indsats_referencer(
        mock_referenser, kun_aktive=True, leverandør_navn=""
    )

    # Should exclude "Afsluttet"
    assert len(aktive) == 2
    assert all(ref["workflowState"]["name"] != "Afsluttet" for ref in aktive)

    # Test filtering by supplier
    med_leverandør = nexus_manager.indsatser.filtrer_indsats_referencer(
        mock_referenser, kun_aktive=False, leverandør_navn="Test Leverandør"
    )

    # Should only include the one with matching supplier
    assert len(med_leverandør) == 1
    assert med_leverandør[0]["workflowState"]["name"] == "Bevilliget"


def test_hent_indsats_error_handling(nexus_manager: NexusClientManager):
    """Test hent_indsats error handling."""
    # Test with invalid reference
    with pytest.raises(ValueError, match="Input er ikke en gyldig indsats reference"):
        nexus_manager.indsatser.hent_indsats({})

    # Test with unknown reference type
    with pytest.raises(ValueError, match="Ukendt reference type"):
        nexus_manager.indsatser.hent_indsats({"type": "unknownType"})


def test_manager_provides_indsats_property():
    """Test that NexusClientManager provides indsats property."""
    from kmd_nexus_client.manager import NexusClientManager

    # Check that manager has indsats property
    assert hasattr(NexusClientManager, "indsatser")


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeIndsatsHttpClient:
    def __init__(self):
        self.api = {"patientGrantById": "patientGrants"}
        self.gets = []
        self.posts = []
        self.indstats = {
            "584": {
                "name": "APV",
                "workflowState": {"name": "Bevilliget"},
                "currentWorkflowTransitions": [
                    {
                        "name": "Annullér",
                        "_links": {"prepareEdit": {"href": "prepare-annuller"}},
                    }
                ],
            }
        }

    def get(self, endpoint):
        self.gets.append(endpoint)
        if endpoint == "prepare-annuller":
            return FakeResponse(
                {
                    "elements": [],
                    "_links": {"save": {"href": "save-annuller"}},
                }
            )
        if endpoint == "prepare-afslut":
            return FakeResponse(
                {
                    "elements": [],
                    "_links": {"save": {"href": "save-afslut"}},
                }
            )
        return FakeResponse(self.indstats[endpoint.rsplit("/", 1)[-1]])

    def post(self, endpoint, json):
        self.posts.append((endpoint, json))
        workflow_state = "Afsluttet" if endpoint == "save-afslut" else "Annulleret"
        return FakeResponse({"savedGrant": {"workflowState": {"name": workflow_state}}})


def test_hent_indsats_ved_id_reads_patient_grant():
    client = FakeIndsatsHttpClient()
    indsatser = IndsatsClient(client)  # type: ignore[arg-type]

    indsats = indsatser.hent_indsats_ved_id("584")

    assert indsats["name"] == "APV"
    assert client.gets == ["patientGrants/584"]


def test_annuller_indsats_uses_supported_transition():
    client = FakeIndsatsHttpClient()
    indsatser = IndsatsClient(client)  # type: ignore[arg-type]
    indsats = client.indstats["584"]

    result = indsatser.annuller_indsats(indsats)

    assert result["savedGrant"]["workflowState"]["name"] == "Annulleret"
    assert client.gets == ["prepare-annuller"]
    assert client.posts == [
        (
            "save-annuller",
            {"elements": [], "_links": {"save": {"href": "save-annuller"}}},
        )
    ]


def test_annuller_indsats_uses_afslut_when_annuller_is_unavailable():
    client = FakeIndsatsHttpClient()
    indsatser = IndsatsClient(client)  # type: ignore[arg-type]
    indsats = {
        "workflowState": {"name": "Bestilt"},
        "currentWorkflowTransitions": [
            {
                "name": "Afslut",
                "_links": {"prepareEdit": {"href": "prepare-afslut"}},
            }
        ],
    }

    result = indsatser.annuller_indsats(indsats)

    assert result["savedGrant"]["workflowState"]["name"] == "Afsluttet"
    assert client.gets == ["prepare-afslut"]
    assert client.posts == [
        (
            "save-afslut",
            {"elements": [], "_links": {"save": {"href": "save-afslut"}}},
        )
    ]


def test_annuller_indsats_is_idempotent_when_already_cancelled():
    client = FakeIndsatsHttpClient()
    indsatser = IndsatsClient(client)  # type: ignore[arg-type]
    indsats = {"workflowState": {"name": "Annulleret"}}

    result = indsatser.annuller_indsats(indsats)

    assert result == {"savedGrant": indsats}
    assert client.gets == []
    assert client.posts == []
