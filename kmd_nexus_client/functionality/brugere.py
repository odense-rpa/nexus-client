from typing import Optional, List
from urllib.parse import quote
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.utils import sanitize_cpr

class BrugereClient:
    """Klient til håndtering af brugere og roller i KMD Nexus."""

    def __init__(self, nexus_client: NexusClient):
        """Initialiserer BrugereClient med en NexusClient instans.

        Args:
            nexus_client: Autentificeret NexusClient til API-kald.
        """
        self.client = nexus_client
    
    def hent_bruger(self, initialer: str) -> Optional[dict]:
        """Henter en bruger baseret på initialer.

        Args:
            initialer: Brugerens initialer (f.eks. "ABC").

        Returns:
            Brugerens data som dict, eller None hvis brugeren ikke findes.

        Raises:
            HTTPStatusError: Ved HTTP-fejl der ikke er 404.
        """
        try:
            encoded_initialer = quote(initialer)
            respone = self.client.get(f"{self.client.api["professionals"]}?query={encoded_initialer}")
            
            bruger = next(
                (a for a in respone.json() if a.get("primaryIdentifier", "").lower() == initialer.lower()),
                None,
            )
            
            if bruger is None:
                return None
            
            bruger = self.client.get(bruger["_links"]["self"]["href"])
            
            return bruger.json()
            
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def hent_bruger_roller(self, bruger: dict) -> Optional[list[dict]]:
        """Henter roller tilknyttet en bruger.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.

        Returns:
            Liste af roller som dicts, eller None hvis brugeren ingen roller har.

        Raises:
            HTTPStatusError: Ved HTTP-fejl der ikke er 404.
        """
        try:                  
            if "roles" not in bruger["_links"]:
                return None
            
            roller = self.client.get(bruger["_links"]["roles"]["href"])
            return roller.json()
            
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def tilføje_rolle_til_bruger(self, bruger: dict, rollenavn: str) -> bool:
        
        nuværende_roller = self.hent_bruger_roller(bruger)
        
        
        # Kontrollere om bruger allerede har rolle
        if nuværende_roller is not None:
            rolle = next(
                (a for a in nuværende_roller if a["name"].lower() == rollenavn.lower()),
                None,
            )
                    
            if rolle is not None:
                return True
        
        mulige_roller = self.client.get(bruger["_links"]["availableRoles"]["href"])
        
        mulige_roller = self.client.get(bruger["_links"]["availableRoles"]["href"]).json()
        
        mulig_rolle = next(
            (a for a in mulige_roller if a["name"].lower() == rollenavn.lower()),
            None,
        )
        
        if mulig_rolle is None:
            return False
        
        body = {
            "added": [mulig_rolle["id"]],
            "removed": []
        }
        
        response = self.client.post(bruger["_links"]["updateRoles"]["href"], body)
        
        return response.status_code == 200       
        
    def fjern_rolle_fra_bruger(self, bruger: dict, rollenavn: str) -> bool:
        """Fjerner en navngivet rolle fra en bruger.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.
            rollenavn: Navnet på rollen der skal fjernes.

        Returns:
            True hvis rollen blev fjernet eller ikke fandtes, False ved fejl.

        Raises:
            ValueError: Hvis brugeren slet ingen roller har.
        """
        roller = self.hent_bruger_roller(bruger)
        
        if roller is None:
            raise ValueError(f"Bruger har ingen roller")
        
        rolle = next(
                (a for a in roller if a["name"].lower() == rollenavn.lower()),
                None,
            )
        
        if rolle is None:
            return True
        
        body = {
            "added": [],
            "removed": [
                rolle["id"]
            ]
        }
        
        response = self.client.post(bruger["_links"]["updateRoles"]["href"], body)
        
        return response.status_code == 200
    
    def fjern_national_rolle_fra_bruger(self, bruger: dict) -> bool:
        """Fjerner den nationale rolle fra en brugers konfiguration.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.

        Returns:
            True hvis den nationale rolle blev fjernet eller ikke var sat, False ved fejl.
        """
        if "configuration" not in bruger["_links"]:
            repsone = self.client.get(bruger["_links"]["self"]["href"])    
            bruger = repsone.json()

        konfiguration = self.client.get(bruger["_links"]["configuration"]["href"])
        
        konfiguration = konfiguration.json()
        
        if konfiguration["nationalRoleConfiguration"] == None:
            return True
        
        konfiguration["nationalRoleConfiguration"] = {
            "nationalRole": None,
            "_links": {}
        }
        
        response = self.client.put(konfiguration["_links"]["update"], konfiguration)
        
        return response.status_code == 200
    
    def hent_bruger_konfiguration(self, bruger: dict) -> dict:
        """Henter konfigurationen for en bruger.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.

        Returns:
            Brugerens konfiguration som dict.
        """
        if "configuration" not in bruger["_links"]:
            repsone = self.client.get(bruger["_links"]["self"]["href"])    
            bruger = repsone.json()
        
        konfiguration = self.client.get(bruger["_links"]["configuration"]["href"])
        
        return konfiguration.json()
    
    def opdater_bruger_konfiguration(self, opdateret_konfiguration: dict) -> dict:
        """Opdaterer konfigurationen for en bruger.

        Args:
            opdateret_konfiguration: Konfiguration-dict som returneret af `hent_bruger_konfiguration`,
                med de ønskede ændringer.

        Returns:
            Den opdaterede konfiguration som dict.
        """
        response = self.client.put(opdateret_konfiguration["_links"]["update"]["href"], opdateret_konfiguration)
        
        return response.json()