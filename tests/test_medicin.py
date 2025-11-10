# Fixtures are automatically loaded from conftest.py

from kmd_nexus_client.manager import NexusClientManager


# Test functions for MedicinClient will be added here
# Available fixtures:
# - nexus_manager: NexusClientManager instance
# - test_borger: Test citizen data
# - base_client: Underlying NexusClient


def test_hent_medicinkort(nexus_manager: NexusClientManager):
    citizen = nexus_manager.borgere.hent_borger("2512489996")
    assert citizen["fullName"] == "Nancy Berggren"

    medicinkort = nexus_manager.medicin.hent_medicinkort(citizen)
    
    assert medicinkort is not None
    assert isinstance(medicinkort, dict)

def test_opdater_medicin(nexus_manager: NexusClientManager):
    citizen = nexus_manager.borgere.hent_borger("2512489996")
    assert citizen["fullName"] == "Nancy Berggren"

    medicinkort = nexus_manager.medicin.hent_medicinkort(citizen)
    medicin = medicinkort["medicationGroups"][0]["medications"][0]

    medicin["remarks"] = "RPA Test"

    nexus_manager.medicin.opdater_medicin(medicin)


def test_filtrer_medicin(nexus_manager: NexusClientManager):
    citizen = nexus_manager.borgere.hent_borger("2512489996")
    assert citizen["fullName"] == "Nancy Berggren"

    medicinkort = nexus_manager.medicin.hent_medicinkort(citizen)
    
    # Test at hente al medicin (ingen specifik gruppe)
    al_medicin = nexus_manager.medicin.filtrer_medicin(medicinkort)
    assert isinstance(al_medicin, list)

    medicin_i_gruppe = nexus_manager.medicin.filtrer_medicin(medicinkort, "Fast medicin")
    assert len(medicin_i_gruppe) == 2
    


