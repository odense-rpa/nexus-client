from datetime import date, timedelta
# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager


def test_hent_kalender(nexus_manager: NexusClientManager, test_borger: dict):
    kalender = nexus_manager.kalender.hent_kalender(test_borger)
    assert kalender is not None


def test_hent_begivenheder(nexus_manager: NexusClientManager, test_borger: dict):
    """Test danske funktion for at hente begivenheder."""
    kalender = nexus_manager.kalender.hent_kalender(test_borger)
    start_dato = date.today()
    slut_dato = start_dato + timedelta(days=30)

    begivenheder = nexus_manager.kalender.hent_begivenheder(kalender, start_dato, slut_dato)
    assert begivenheder is not None

