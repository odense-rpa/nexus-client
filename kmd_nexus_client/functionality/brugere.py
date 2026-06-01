from typing import Optional, List
from urllib.parse import quote
from httpx import HTTPStatusError

from kmd_nexus_client.client import NexusClient
from kmd_nexus_client.utils import sanitize_cpr

class BrugereClient:
    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client
    
    def hent_bruger(self, initialer: str) -> Optional[dict]:
        
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
    
    def hent_bruger_roller(self, bruger:dict) -> Optional[list[dict]]:
        
        try:                  
            if "roles" not in bruger["_links"]:
                return None
            
            roller = self.client.get(bruger["_links"]["roles"]["href"])
            return roller.json()
            
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        
    def fjern_rolle_fra_bruger(self, bruger: dict, rollenavn: str) -> bool:
        
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
    