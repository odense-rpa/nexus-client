import pytest

from datetime import date, timedelta, datetime, timezone
# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.manager import NexusClientManager
from kmd_nexus_client.functionality.kalender import KalenderClient


def test_hent_kalender(nexus_manager: NexusClientManager, test_borger: dict):
    kalender = nexus_manager.kalender.hent_kalender(test_borger)
    assert kalender is not None

def test_get_citizen_calendar_backward_compatibility(nexus_manager: NexusClientManager, test_borger: dict):
    """Test backward compatibility for old method name."""
    # Test that old method name still works
    calendar = nexus_manager.kalender.get_citizen_calendar(test_borger)
    assert calendar is not None
    # Verify it returns same result as Danish method
    kalender = nexus_manager.kalender.hent_kalender(test_borger)
    assert kalender is not None
    # Verify both methods return valid calendar objects with same basic structure
    assert "id" in calendar
    assert "id" in kalender
    assert calendar["id"] == kalender["id"]

def test_hent_begivenheder(nexus_manager: NexusClientManager, test_borger: dict):
    """Test danske funktion for at hente begivenheder."""
    kalender = nexus_manager.kalender.hent_kalender(test_borger)
    start_dato = date.today()
    slut_dato = start_dato + timedelta(days=30)

    begivenheder = nexus_manager.kalender.hent_begivenheder(kalender, start_dato, slut_dato)
    assert begivenheder is not None

def test_events_backward_compatibility(nexus_manager: NexusClientManager, test_borger: dict):
    """Test backward compatibility for old method name."""
    citizen_calendar = nexus_manager.kalender.hent_kalender(test_borger)
    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    # Test that old method name still works
    events = nexus_manager.kalender.events(citizen_calendar, start_date, end_date)
    assert events is not None
    # Verify it returns same result as Danish method
    begivenheder = nexus_manager.kalender.hent_begivenheder(citizen_calendar, start_date, end_date)
    assert begivenheder is not None
    # Verify both methods return valid event lists with same structure
    assert isinstance(events, list)
    assert isinstance(begivenheder, list)
    assert len(events) == len(begivenheder)
