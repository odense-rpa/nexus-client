from datetime import datetime, timezone
from typing import Optional, List
from kmd_nexus_client.client import NexusClient


class MedicinClient:
    """
    Klient til medicin-operationer i KMD Nexus.

    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.medicin.hent_medicin(...)
    """

    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

        
    def hent_medicinkort(self, borger:dict) -> dict:
        """
        Hent medicinkort på en borger

        :param borger: Borgerens vis medicinkort der skalbruges.
        :return: Det fundne medicinkort objekt på borger.
        """
        
        medicinkort = self.client.get(borger["_links"]["medicationCard"]["href"])
        return medicinkort.json()

    def opdater_medicin(self, medicin:dict) -> dict:
        link = medicin["_links"]["self"]["href"]
        medicin = self.client.put(link, medicin)

        return medicin.json()
    
    def filtrer_medicin(self, medicinkort: dict, medicingruppe: Optional[str] = None) -> List[dict]:
        """
        Filtrer medicin fra medicinkort baseret på medicingruppe.

        :param medicinkort: Medicinkort objekt med medicationGroups
        :param medicingruppe: Navn på den specifikke medicingruppe at filtrere efter. 
                             Hvis None, returneres al medicin fra alle grupper.
        :return: Liste af medicin objekter
        """
        medicin = []
        
        # Tjek om medicationGroups findes i medicinkort
        if "medicationGroups" not in medicinkort:
            return medicin
        
        for group in medicinkort["medicationGroups"]:
            # Hvis ingen specifik gruppe er angivet, saml medicin fra alle grupper
            if medicingruppe is None:
                if "medications" in group:
                    medicin.extend(group["medications"])
            # Hvis en specifik gruppe er angivet, kun inkluder medicin fra den gruppe
            else:
                # Tjek om gruppenavnet matcher (case-insensitive)
                group_name = group["displayName"].lower()
                if group_name == medicingruppe.lower() and "medications" in group:
                    medicin.extend(group["medications"])
        
        return medicin
        