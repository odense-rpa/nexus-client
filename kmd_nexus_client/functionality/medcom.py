from typing import Optional, List, Dict, Any
from httpx import HTTPStatusError
import base64

from kmd_nexus_client.client import NexusClient


class MedComClient:
    """
    Klient til MedCom-operationer i KMD Nexus.
    
    MedCom beskeder følger danske standarder for elektronisk kommunikation 
    i sundhedssektoren og har en specifik lifecycle og navigation struktur.
    
    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.medcom.hent_indbakke(...)
    """
    
    def __init__(self, nexus_client: NexusClient):
        self.client = nexus_client

    def hent_indbakke(self, borger: dict) -> Optional[dict]:
        """
        Hent MedCom indbakke for en borger med pagination info.

        :param borger: Borgeren der skal hentes indbakke for.
        :return: Indbakke med pagination info, eller None hvis hentning fejlede.
        """
        try:
            response = self.client.get(borger["_links"]["inboxMessages"]["href"])
            return response.json()
        except HTTPStatusError:
            return None

    def hent_alle_beskeder(self, borger: dict) -> List[dict]:
        """
        Hent alle MedCom beskeder for en borger ved at gennemgå alle sider.

        :param borger: Borgeren der skal hentes beskeder for.
        :return: Liste af alle beskeder fra indbakken.
        """
        beskeder = []
        
        # Hent indbakke med pagination
        indbakke = self.hent_indbakke(borger)
        if not indbakke:
            return beskeder

        # Gennemgå alle sider
        for side in indbakke.get("pages", []):
            try:
                # Hent indhold af siden
                side_response = self.client.get(side["_links"]["self"]["href"])
                besked_referencer = side_response.json()
                
                # Hent hver besked fra referencerne
                for besked_ref in besked_referencer:
                    try:
                        besked_response = self.client.get(besked_ref["_links"]["self"]["href"])
                        fuld_besked = besked_response.json()
                        beskeder.append(fuld_besked)
                    except HTTPStatusError:
                        continue  # Skip denne besked hvis der er fejl
                        
            except HTTPStatusError:
                continue  # Skip denne side hvis der er fejl
                
        return beskeder

    def hent_besked(self, besked_reference: dict) -> Optional[dict]:
        """
        Hent en specifik MedCom besked fra en reference.

        :param besked_reference: Reference til beskeden.
        :return: Fuld besked, eller None hvis hentning fejlede.
        """
        try:
            response = self.client.get(besked_reference["_links"]["self"]["href"])
            return response.json()
        except HTTPStatusError:
            return None

    def dekoder_medcom_xml(self, besked: dict) -> Optional[str]:
        """
        Dekoder MedCom XML indholdet fra en besked.

        :param besked: MedCom beskeden der indeholder base64 encoded XML.
        :return: Dekoderet XML som string, eller None hvis dekodning fejlede.
        """
        try:
            raw_data = besked.get("raw")
            if not raw_data:
                return None
            
            # Base64 dekod XML indholdet
            decoded_bytes = base64.b64decode(raw_data)
            return decoded_bytes.decode('utf-8')
        except Exception:
            return None

    def accepter_besked(self, besked: dict) -> bool:
        """
        Accepter en MedCom besked (markerer som læst/behandlet).

        :param besked: Beskeden der skal accepteres.
        :return: True hvis succesfuldt accepteret, False ellers.
        """
        try:
            # Check om accept link findes
            if "accept" not in besked.get("_links", {}):
                return False
            
            response = self.client.put(
                besked["_links"]["accept"]["href"],
                json=besked
            )
            return response.status_code == 200
        except HTTPStatusError:
            return False

    def arkiver_besked(self, besked: dict) -> bool:
        """
        Arkiver en MedCom besked (fjerner fra aktiv indbakke).

        :param besked: Beskeden der skal arkiveres.
        :return: True hvis succesfuldt arkiveret, False ellers.
        """
        try:
            # Check om archive link findes
            if "archive" not in besked.get("_links", {}):
                return False
            
            response = self.client.post(
                besked["_links"]["archive"]["href"],
                json=besked
            )
            return response.status_code == 200
        except HTTPStatusError:
            return False

    def hent_tilgaengelige_forloeb(self, besked: dict) -> List[dict]:
        """
        Hent tilgængelige forløb for en MedCom besked.

        :param besked: Beskeden der skal hentes tilgængelige forløb for.
        :return: Liste af tilgængelige forløb.
        """
        try:
            pathway_links = besked.get("pathwayAssociation", {}).get("_links", {})
            if "availablePathwayAssociation" not in pathway_links:
                return []
            
            response = self.client.get(
                pathway_links["availablePathwayAssociation"]["href"]
            )
            return response.json()
        except HTTPStatusError:
            return []

    def tildel_til_forloeb(self, besked: dict, forloeb_id: str, forloeb_navn: str = "MedCom") -> bool:
        """
        Tildel en MedCom besked til et specifikt forløb.

        :param besked: Beskeden der skal tildeles.
        :param forloeb_id: ID på forløbet (programPathwayId).
        :param forloeb_navn: Navn på forløbet (standard: "MedCom").
        :return: True hvis succesfuldt tildelt, False ellers.
        """
        try:
            # Modificer besked for at tildele til forløb
            modificeret_besked = besked.copy()
            
            # Sikr at pathwayAssociation eksisterer
            if "pathwayAssociation" not in modificeret_besked:
                modificeret_besked["pathwayAssociation"] = {}
            
            # Sæt placement
            modificeret_besked["pathwayAssociation"]["placement"] = {
                "programPathwayId": forloeb_id,
                "name": forloeb_navn
            }
            
            # Opdater besked
            response = self.client.put(
                besked["_links"]["self"]["href"],
                json=modificeret_besked
            )
            return response.status_code == 200
        except HTTPStatusError:
            return False

    def tildel_til_forloeb_ved_navn(self, besked: dict, forloeb_navn: str) -> bool:
        """
        Tildel en MedCom besked til et forløb ved at finde det via navn.

        :param besked: Beskeden der skal tildeles.
        :param forloeb_navn: Navn på forløbet der skal findes.
        :return: True hvis succesfuldt tildelt, False ellers.
        """
        # Hent tilgængelige forløb
        tilgaengelige_forloeb = self.hent_tilgaengelige_forloeb(besked)
        
        # Find forløb med matchende navn
        target_forloeb = None
        for forloeb in tilgaengelige_forloeb:
            if forloeb.get("name") == forloeb_navn:
                target_forloeb = forloeb
                break
        
        if not target_forloeb:
            return False
        
        # Tildel til fundet forløb
        return self.tildel_til_forloeb(
            besked, 
            target_forloeb["programPathwayId"], 
            forloeb_navn
        )

    def filtrer_beskeder(self, beskeder: List[dict], **kriterier) -> List[dict]:
        """
        Filtrer MedCom beskeder baseret på kriterier.

        :param beskeder: Liste af beskeder der skal filtreres.
        :param kriterier: Filterkriterier (subject, har_forloeb, etc.).
        :return: Filtrerede beskeder.
        """
        filtrerede = []
        
        for besked in beskeder:
            match = True
            
            # Filtrer på emne
            if "subject" in kriterier:
                if kriterier["subject"].lower() not in besked.get("subject", "").lower():
                    match = False
            
            # Filtrer på om besked har forløbstilknytning
            if "har_forloeb" in kriterier:
                har_placement = bool(
                    besked.get("pathwayAssociation", {}).get("placement")
                )
                if kriterier["har_forloeb"] != har_placement:
                    match = False
            
            # Filtrer på specifikt forløb navn
            if "forloeb_navn" in kriterier:
                placement = besked.get("pathwayAssociation", {}).get("placement", {})
                if placement.get("name") != kriterier["forloeb_navn"]:
                    match = False
            
            if match:
                filtrerede.append(besked)
        
        return filtrerede

    def get_besked_statistik(self, borger: dict) -> Dict[str, Any]:
        """
        Hent statistik for MedCom beskeder for en borger.

        :param borger: Borgeren der skal hentes statistik for.
        :return: Dictionary med statistik.
        """
        beskeder = self.hent_alle_beskeder(borger)
        
        total = len(beskeder)
        med_forloeb = len([b for b in beskeder if b.get("pathwayAssociation", {}).get("placement")])
        uden_forloeb = total - med_forloeb
        
        # Gruppér efter forløb
        forloeb_grupper = {}
        for besked in beskeder:
            placement = besked.get("pathwayAssociation", {}).get("placement")
            if placement:
                navn = placement.get("name", "Ukendt")
                forloeb_grupper[navn] = forloeb_grupper.get(navn, 0) + 1
        
        return {
            "total_beskeder": total,
            "med_forloeb": med_forloeb,
            "uden_forloeb": uden_forloeb,
            "forloeb_fordeling": forloeb_grupper
        }
