from typing import List
from datetime import date, datetime, timedelta

from kmd_nexus_client.client import NexusClient


class KalenderClient:
    """
    Klient til kalender-operationer i KMD Nexus.
    
    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.kalender.hent_begivenheder(...)
    """
    def __init__(self, nexus_client: NexusClient):
        self.nexus_client = nexus_client

    # TODO: Port alle funktioner og refactor dem
    
    def hent_kalender(self, borger: dict, kalender_navn: str = "Borgerkalender") -> dict:
        """
        Hent kalender for borgeren.
        
        :param borger: Borgeren der skal hentes kalender for.
        :param kalender_navn: Navnet på kalenderen (standard: "Borgerkalender").
        :return: Borgerens kalender.
        """
        # Find citizen preferences
        citizen_preferences = self._hent_præferencer(borger)

        # Find kalender i citizen preferences
        calendar = next(
            (item 
            for item in citizen_preferences["CITIZEN_CALENDAR"] 
            if item["name"] == kalender_navn), None
        )
        if not calendar:
            raise ValueError(f"Kalender {kalender_navn} ikke fundet i borgerens præferencer.")
        
        # Get detailed calendar
        response = self.nexus_client.get(calendar["_links"]["self"]["href"])
        
        return response.json()

    def hent_begivenheder(self, kalender: dict, start_dato: date, slut_dato: date) -> dict:
        """
        Hent begivenheder fra en kalender.
        
        :param kalender: Kalenderen der skal hentes begivenheder fra.
        :param start_dato: Startdato for begivenhederne.
        :param slut_dato: Slutdato for begivenhederne.
        :return: Begivenhederne fra kalenderen.
        """
                
        # Validate if calendar contains events link:
        if "events" not in kalender["_links"]:
            raise ValueError("Kalender indeholder ikke events link.")
        
        # Sanitize url for Nexus
        url = f"{kalender['_links']['events']['href']}?from={start_dato.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'}&to={slut_dato.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'}"
        
        # Get events
        return self.nexus_client.get(url).json()["eventResources"]
    
    def _hent_præferencer(self, borger: dict) -> dict:
        """
        Hent præferencer for borgeren (privat hjælpefunktion).
        
        :param borger: Borgeren der skal hentes præferencer for.
        :return: Borgerens præferencer.
        """
        response = self.nexus_client.get(borger["_links"]["patientPreferences"]["href"])
        return response.json()
        