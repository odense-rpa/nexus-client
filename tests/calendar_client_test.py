import pytest

from datetime import date, timedelta, datetime, timezone
from .fixtures import calendar_client, base_client, test_citizen, citizens_client  # noqa
from kmd_nexus_client.functionality.calendar import CalendarClient


def test_get_citizen_calendar(calendar_client: CalendarClient, test_citizen: dict):
    citizen = test_citizen
    calendar = calendar_client.get_citizen_calendar(citizen)
    assert calendar is not None

def test_get_events(calendar_client: CalendarClient, test_citizen: dict):
    # Test getting events from Nancy's calendar from today and 30 out forward. 
    # Might have to manually add calendar event in UI to pass test... 
    citizen = test_citizen
    citizen_calendar = calendar_client.get_citizen_calendar(citizen)
    start_date = date.today()
    end_date = start_date + timedelta(days=30)

    events = calendar_client.events(citizen_calendar, start_date, end_date)
    assert events is not None
