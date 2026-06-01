from kmd_nexus_client.manager import NexusClientManager


def test_hent_bruger(nexus_manager: NexusClientManager, test_initialer: str):
    bruger = nexus_manager.brugere.hent_bruger(test_initialer)

    assert bruger is not None
    assert bruger["initials"] == test_initialer
    
def test_hent_bruger_roller(nexus_manager: NexusClientManager, test_initialer: str):
    
    bruger = nexus_manager.brugere.hent_bruger(test_initialer)
    
    assert bruger is not None
    
    roller = nexus_manager.brugere.hent_bruger_roller(bruger)
    
    assert roller is not None
    assert isinstance(roller, list)
    assert len(roller) > 0

def test_fjern_rolle_fra_bruger(nexus_manager: NexusClientManager, test_initialer: str):
    bruger = nexus_manager.brugere.hent_bruger("")
    assert bruger is not None
    
    # Test kun på bruger du ved skal have fjernet en rolle
    nexus_manager.brugere.fjern_rolle_fra_bruger(bruger, "test")

def test_fjern_nationale_rolle(nexus_manager: NexusClientManager, test_initialer: str):
    bruger = nexus_manager.brugere.hent_bruger("mekso")
    assert bruger is not None
    
    fjernet = nexus_manager.brugere.fjern_national_rolle_fra_bruger(bruger)
    
    assert fjernet is True