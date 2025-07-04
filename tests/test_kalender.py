import pytest

from datetime import date, timedelta, datetime, timezone
# Fixtures are automatically loaded from conftest.py
from kmd_nexus_client.functionality.kalender import KalenderClient


def test_hent_kalender(kalender_client: KalenderClient, test_borger: dict):
    borger = test_borger
    kalender = kalender_client.hent_kalender(borger)
    assert kalender is not None

def test_get_citizen_calendar_backward_compatibility(kalender_client: KalenderClient, test_borger: dict):
    """Test backward compatibility for old method name."""
    citizen = test_borger
    # Test that old method name still works
    calendar = kalender_client.get_citizen_calendar(citizen)
    assert calendar is not None
    # Verify it returns same result as Danish method
    kalender = kalender_client.hent_kalender(citizen)
    assert calendar == kalender

def test_hent_begivenheder(kalender_client: KalenderClient, test_borger: dict):
    """Test danske funktion for at hente begivenheder."""
    borger = test_borger
    kalender = kalender_client.hent_kalender(borger)
    start_dato = date.today()
    slut_dato = start_dato + timedelta(days=30)

    begivenheder = kalender_client.hent_begivenheder(kalender, start_dato, slut_dato)
    assert begivenheder is not None

def test_events_backward_compatibility(kalender_client: KalenderClient, test_borger: dict):
    """Test backward compatibility for old method name."""
    citizen = test_borger
    citizen_calendar = kalender_client.hent_kalender(citizen)
    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    # Test that old method name still works
    events = kalender_client.events(citizen_calendar, start_date, end_date)
    assert events is not None
    # Verify it returns same result as Danish method
    begivenheder = kalender_client.hent_begivenheder(citizen_calendar, start_date, end_date)
    assert events == begivenheder
