import pytest

from datetime import date, timedelta, datetime, timezone
from .fixtures import calendar_client, base_client, test_citizen, citizens_client  # noqa
from kmd_nexus_client.functionality.kalender import KalenderClient


def test_hent_kalender(calendar_client: KalenderClient, test_citizen: dict):
    borger = test_citizen
    kalender = calendar_client.hent_kalender(borger)
    assert kalender is not None

def test_get_citizen_calendar_backward_compatibility(calendar_client: KalenderClient, test_citizen: dict):
    """Test backward compatibility for old method name."""
    citizen = test_citizen
    calendar = calendar_client.get_citizen_calendar(citizen)
    assert calendar is not None

def test_hent_begivenheder(calendar_client: KalenderClient, test_citizen: dict):
    """Test danske funktion for at hente begivenheder."""
    borger = test_citizen
    kalender = calendar_client.hent_kalender(borger)
    start_dato = date.today()
    slut_dato = start_dato + timedelta(days=30)

    begivenheder = calendar_client.hent_begivenheder(kalender, start_dato, slut_dato)
    assert begivenheder is not None

def test_events_backward_compatibility(calendar_client: KalenderClient, test_citizen: dict):
    """Test backward compatibility for old method name."""
    citizen = test_citizen
    citizen_calendar = calendar_client.get_citizen_calendar(citizen)
    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    events = calendar_client.events(citizen_calendar, start_date, end_date)
    assert events is not None
