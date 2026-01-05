import pytest

from kmd_nexus_client.manager import NexusClientManager

def test_hent_aktivitetsliste_elementer(nexus_manager: NexusClientManager):
    aktivitetsliste = nexus_manager.aktivitetslister.hent_aktivitetsliste(
        navn="MedCom - Korrespondancer: venter + accepterede",
        organisation=None,
        medarbejder=None,
        antal_sider=50
    )

    assert aktivitetsliste is not None
    assert isinstance(aktivitetsliste, list)
    assert len(aktivitetsliste) > 0
