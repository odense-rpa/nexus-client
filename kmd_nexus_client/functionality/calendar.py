from typing import List
from datetime import date, datetime, timedelta

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.functionality.citizens import CitizensClient


class CalendarClient:
    def __init__(self, nexus_client: NexusClient, citizens_client: CitizensClient):
        self.nexus_client = nexus_client
        self.citizens_client = citizens_client
    
    def get_citizen_calendar(self, citizen: dict, calendar_name = "Borgerkalender") -> dict:
        """
        Get calendar for a citizen.
        
        :param citizen: The citizen to retrieve calendar for.
        :param calendar_name: The name of the calendar to retrieve. Default is "Borgerkalender".
        :return: The calendar for the citizen.
        """

        # Find citizen preferences
        citizen_preferences = self.citizens_client.get_citizen_preferences(citizen=citizen)

        # Find borgerkalender in citizen preferences
        calendar = next(
            (item 
            for item in citizen_preferences["CITIZEN_CALENDAR"] 
            if item["name"] == calendar_name), None
        )
        if not calendar:
            raise ValueError(f"Calendar {calendar_name} not found in citizen preferences.")
        
        # Get detailed calendar
        response = self.nexus_client.get(calendar["_links"]["self"]["href"])
        
        return response.json()

    def events(self, calendar: dict, start_date: date, end_date: date) -> dict:
        """
        Get events from a calendar.
        
        :param calendar: The calendar to retrieve events from.
        :param start_date: The start date for the events. Default is today.
        :param end_date: The end date for the events. Default is 30 days from today.
        :return: The events from the calendar.
        """
                
        # Validate if calendar contains events link:
        if "events" not in calendar["_links"]:
            raise ValueError("Calendar does not contain events link.")
        
        # Sanitize url for Nexus
        url = f"{calendar['_links']['events']['href']}?from={start_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'}&to={end_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'}"
        
        # Get events
        return self.nexus_client.get(url).json()["eventResources"]
        