import pytest

from kmd_nexus_client.functionality.tilstande import Tilstandsgruppe
from kmd_nexus_client.manager import NexusClientManager


def test_hent_tilstande(nexus_manager: NexusClientManager, test_borger: dict):
    assert "patientConditions" in test_borger["_links"]

    # Test the actual method
    tilstande = nexus_manager.tilstande.hent_tilstande(test_borger)

    # Should not raise an exception and should return valid response
    assert isinstance(tilstande, list)
    assert all(isinstance(t, dict) for t in tilstande)


def test_hent_tilstandstyper(nexus_manager: NexusClientManager, test_borger: dict):
    assert "availableConditionClassifications" in test_borger["_links"]

    # Test the actual method
    tilstandstyper = nexus_manager.tilstande.hent_tilstandstyper(test_borger)

    # Should not raise an exception and should return valid response
    assert isinstance(tilstandstyper, list)
    assert len(tilstandstyper) > 0
    assert all(isinstance(t, dict) for t in tilstandstyper)


def test_opret_tilstand(nexus_manager: NexusClientManager, test_borger: dict):
    tilstandstyper = nexus_manager.tilstande.hent_tilstandstyper(test_borger)
    assert len(tilstandstyper) > 0

    tilstandstype = [
        t
        for t in tilstandstyper
        if t["name"] == "Energi og handlekraft" and t["klMappingCode"] == "J4.6"
    ][0]

    # Test the actual method
    ny_tilstand = nexus_manager.tilstande.opret_tilstand(test_borger, tilstandstype)

    # Should not raise an exception and should return valid response
    assert isinstance(ny_tilstand, dict)


def test_rediger_tilstand(nexus_manager: NexusClientManager, test_borger: dict):
    tilstande = nexus_manager.tilstande.hent_tilstande(test_borger)
    assert len(tilstande) > 0
    ny_tilstand = tilstande[0]

    # Test the actual method
    redigeret_tilstand = nexus_manager.tilstande.rediger_tilstand(
        ny_tilstand,
        status="PCActive",
        expectedLevelDescription="Dette er fritekst",
        currentLevel="LightLimitations",
    )

    # Should not raise an exception and should return valid response
    assert isinstance(redigeret_tilstand, dict)
    assert redigeret_tilstand["expectedLevelDescription"] == "Dette er fritekst"


def test_hent_tilstandsgruppe(nexus_manager: NexusClientManager, test_borger: dict):
    for gruppe in Tilstandsgruppe:
        if gruppe.value not in test_borger["_links"]:
            continue
        result = nexus_manager.tilstande.hent_tilstandsgrupper(test_borger, gruppe)
        assert isinstance(result, (dict, list))
        assert 'conditionGroupVisitation' in result
        assert len(result['conditionGroupVisitation']) > 0
        # We must have real conditions, with real endpoints - this checks it.
        assert 'activate' in result['conditionGroupVisitation'][0]['conditions'][0]['_links']


def test_opdater_tilstandsgruppe(nexus_manager: NexusClientManager, test_borger: dict):
    grupper = nexus_manager.tilstande.hent_tilstandsgrupper(test_borger, Tilstandsgruppe.GENOPTRÆNING)

    if "visit" not in grupper.get("_links", {}):
        pytest.skip("Tilstandsgruppe understøtter ikke visit-opdatering")
    
    for visitation in grupper.get("conditionGroupVisitation", []):
        for condition in visitation.get("conditions", []):
            
            if condition.get("classification", {}).get("name") == "Personlig pleje":
                condition["state"] = "ACTIVE"
                break
            
            # relaterede_aktiviteter = nexus_manager.nexus_client.get(condition.get("_links", {}).get("relatedActivities", []).get("href", "")).json()
            #     for kategori in relaterede_aktiviteter:
            #         if kategori.get("groupName") == "Indsatser":
            #             for aktivitet in kategori.get("citizenActivitiesGroups", []):
            #                 for aktivitet_item in aktivitet.get("activities", []):                                
            #                     nexus_manager.nexus_client.delete(aktivitet_item["_links"]["deleteActivityLink"]["href"])

    nexus_manager.tilstande.opdater_tilstandsgrupper(grupper)
