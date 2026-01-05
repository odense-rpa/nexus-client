import json

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from httpx import HTTPStatusError
from kmd_nexus_client.client import NexusClient

if TYPE_CHECKING:
    from kmd_nexus_client.manager import NexusClientManager

class SkemaerClient:
    """
    Klient til skema-operationer i KMD Nexus.
    
    Håndterer oprettelse, redigering, hentning og sletning af skemaer
    samt udfyldning og submission af skemaer.

    VIGTIGT: Opret ikke denne klasse direkte!
    Brug NexusClientManager: nexus.skemaer.hent_skema(...)
    """

    def __init__(self, nexus_client: NexusClient, manager: Optional["NexusClientManager"] = None):
        self.client = nexus_client
        self._manager = manager

    def hent_skemadefinition_uden_forløb(self, borger: dict) -> List[dict]:
        """
        Hent alle tilgængelige skematyper (form definitions) for et objekt.

        :param objekt: Objekt at hente skematyper for (borger, forløb/pathway reference, etc.).
        :return: Liste af tilgængelige skematyper.
        """
        if "availableFormDefinitions" not in borger.get("_links", {}):
            raise ValueError("Objekt indeholder ikke availableFormDefinitions link.")
        
        response = self.client.get(borger["_links"]["availableFormDefinitions"]["href"])
        return response.json()
    
    def hent_skemadefinition_på_forløb(self, grundforløb: str, forløb: str, borger: dict) -> List[dict]:
        """
        Hent alle tilgængelige skematyper (form definitions) for et objekt inden for et specifikt forløb.

        :param grundforløb: ID eller navn på grundforløb.
        :param forløb: ID eller navn på forløb.
        :param objekt: Objekt at hente skematyper for (borger, pathway reference, etc.).
        :return: Liste af tilgængelige skematyper inden for det angivne forløb.
        """
        if "availableFormDefinitions" not in borger.get("_links", {}):
            raise ValueError("Objekt indeholder ikke availableFormDefinitions link.")

        # Tilgå BorgerClient gennem manager hvis tilgængelig, ellers opret direkte
        if self._manager is not None:
            borgere_client = self._manager.borgere
        else:
            # Fallback: opret BorgerClient direkte (ikke anbefalet men funktionelt)
            from kmd_nexus_client.functionality.borgere import BorgerClient
            borgere_client = BorgerClient(self.client)
            
        visning = borgere_client.hent_visning(borger=borger, visnings_navn="-Aktive forløb")
        referencer = borgere_client.hent_referencer(visning=visning)

        # Find den specifikke grundforløbsreference (første match)
        grundforløb_ref = next((ref for ref in referencer if ref.get("name") == grundforløb or ref.get("id") == grundforløb and ref.get("type") == "patientPathwayReference"), None)
        if not grundforløb_ref:
            raise ValueError(f"Ingen referencer fundet for det angivne grundforløb: {grundforløb}")

        # Nu søg i det specifikke grundforløbs børn efter forløbet
        forløb_refs = next((child for child in grundforløb_ref.get("children", []) if child.get("name") == forløb or child.get("id") == forløb and child.get("type") == "patientPathwayReference"), None)
        if not forløb_refs:
            raise ValueError(f"Ingen forløb fundet for: {forløb}")

        referencer = self.client.get(forløb_refs["_links"]["self"]["href"]).json()

        skemadefinitioner = self.client.get(referencer["_links"]["availableFormDefinitions"]["href"]).json()
        
        return skemadefinitioner

    def hent_skema_fra_reference(self, reference: dict) -> dict:
        """
        Hent skemainstans fra en pathway reference.

        :param reference: Reference til skemaet i pathway systemet.
        :return: Skemainstans med alle felter og data.
        """
        if "referencedObject" not in reference.get("_links", {}):
            raise ValueError("Reference indeholder ikke referencedObject link.")
            
        response = self.client.get(reference["_links"]["referencedObject"]["href"])
        return response.json()

    def hent_skema_prototype(self, skematype: dict) -> dict:
        """
        Hent skema prototype for at oprette nyt skema baseret på skematype.

        :param skematype: Skematype (form definition) fra availableFormDefinitions.
        :return: Skema prototype klar til udfyldelse.
        """
        if "formDataPrototype" not in skematype.get("_links", {}):
            raise ValueError("Skematype indeholder ikke formDataPrototype link.")

        response = self.client.get(skematype["_links"]["formDataPrototype"]["href"])
        return response.json()

    def hent_tilgængelige_handlinger(self, prototype: dict) -> List[dict]:
        """
        Hent tilgængelige handlinger for et skema prototype.

        :param prototype: Skema prototype fra hent_skema_prototype().
        :return: Liste af tilgængelige handlinger.
        """
        if "availableActions" not in prototype.get("_links", {}):
            raise ValueError("Prototype indeholder ikke availableActions link.")
            
        response = self.client.get(prototype["_links"]["availableActions"]["href"])
        return response.json()

    def udfyld_skema_felter(self, prototype: dict, data: Dict[str, Any]) -> dict:
        """
        Udfyld et skema prototype med data baseret på felttyper.

        :param prototype: Skema prototype der skal udfyldes.
        :param data: Dictionary med feltnavne (labels) og værdier.
        :return: Opdateret prototype med udfyldt data.
        """
        for item in prototype.get("items", []):
            label = item.get("label")
            if label in data:
                field_type = item.get("type")
                value = data[label]
                
                if field_type in ["radioGroup", "dropDown"]:
                    # Sæt item["value"] hvis en af possibleValues har name == value, ellers fejl
                    possible_values = item.get("possibleValues", [])
                    for v in possible_values:
                        if v.get("name") == value:
                            item["value"] = v
                            break
                    else:
                        raise ValueError(f"Værdi '{value}' er ikke gyldig for felt '{label}'. Gyldige navne: {[v.get('name') for v in possible_values]}")
                elif field_type in ["checkGroup"]:
                    possible_values = item.get("possibleValues", [])
                    values = []                    
                    for v in possible_values:
                        if v.get("name") == value:
                            values.append(v)

                    item["value"] = values

                elif field_type == "date":
                    # Accept datetime and format as UTC ISO string
                    from datetime import datetime, timezone
                    if isinstance(value, datetime):
                        item["value"] = value.astimezone(timezone.utc).isoformat()
                    else:
                        raise ValueError(f"Ugyldig datoformat for felt '{label}': {value}")
                else:
                    # Standard tekstfelter og andre simple typer
                    item["value"] = value
                    
        return prototype

    def _opret_skema(self, prototype: dict, handling: dict) -> dict:
        """
        PRIVAT METODE - brug opret_komplet_skema() i stedet. 

        Opret et nyt skema baseret på udfyldt prototype og valgt handling.

        :param prototype: Udfyldt skema prototype fra udfyld_skema_felter().
        :param handling: Handling fra hent_tilgængelige_handlinger().
        :return: Oprettet skema instans.
        """
        if "createFormData" not in handling.get("_links", {}):
            raise ValueError("Handling indeholder ikke createFormData link.")
            
        response = self.client.post(
            handling["_links"]["createFormData"]["href"], 
            json=prototype
        )
        return response.json()

    def hent_skema_historik(self, skema: dict) -> List[dict]:
        """
        Hent revisionshistorik/audit trail for et skema.

        :param skema: Skema instans at hente historik for.
        :return: Liste af historiske ændringer og events.
        """
        if "audit" not in skema.get("_links", {}):
            raise ValueError("Skema indeholder ikke audit link.")
            
        response = self.client.get(skema["_links"]["audit"]["href"])
        return response.json().get("auditEntries", [])

    def opret_komplet_skema(
        self, 
        borger: dict, 
        skematype_navn: str, 
        handling_navn: str, 
        data: Dict[str, Any],
        grundforløb: Optional[str] = None,
        forløb: Optional[str] = None
    ) -> dict:
        """
        Komplet skema oprettelsesprocess i ét kald - implementerer den 5-trins process.

        :param objekt: Objekt at oprette skema for (borger eller pathway reference).
        :param skematype_navn: Navn på skematype (f.eks. "Observation").
        :param handling_navn: Navn på handling (f.eks. "Aktivt").
        :param data: Dictionary med feltdata til udfyldelse.
        :param grundforløb: (valgfri) Grundforløb hvis skema er på et forløb.
        :param forløb: (valgfri) Forløb hvis skema er på et forløb.
        :return: Oprettet skema instans.
        """
        # Trin 1: Hent tilgængelige skematyper
        if grundforløb and forløb:
            skematyper = self.hent_skemadefinition_på_forløb(
                grundforløb=grundforløb,
                forløb=forløb,
                borger=borger,
            )
        else:
            skematyper = self.hent_skemadefinition_uden_forløb(borger)
        skematype = self._find_skematype_by_name(skematyper, skematype_navn)
        if not skematype:
            raise ValueError(f"Skematype '{skematype_navn}' ikke fundet.")
        
        # Trin 2: Hent prototype
        prototype = self.hent_skema_prototype(skematype)
        
        # Trin 3: Hent tilgængelige handlinger
        handlinger = self.hent_tilgængelige_handlinger(prototype)
        handling = self._find_handling_by_name(handlinger, handling_navn)
        if not handling:
            raise ValueError(f"Handling '{handling_navn}' ikke fundet.")
        
        # Trin 4: Udfyld prototype
        udfyldt_prototype = self.udfyld_skema_felter(prototype, data)
        
        # Trin 5: Opret skema
        return self._opret_skema(udfyldt_prototype, handling)
    
    def rediger_skema(self, skema: dict, handling_navn: str, data: Dict[str, Any]) -> dict:
        """
        Rediger et eksisterende skema med nye data.

        :param skema: Eksisterende skema instans.
        :param handling_navn: Navn på handling der skal udføres ved opdatering.
        :param data: Dictionary med feltdata til opdatering.
        :return: Opdateret skema instans.
        """

        skema = self.client.hent_fra_reference(skema)        
        handlinger = self.hent_tilgængelige_handlinger(skema)

        handling = self._find_handling_by_name(handlinger, handling_navn)
        if not handling:
            raise ValueError(f"Handling '{handling_navn}' ikke fundet.")
        
        udfyldt_skema = self.udfyld_skema_felter(skema, data)
        
        response = self.client.put(
            handling["_links"]["updateFormData"]["href"],
            json=udfyldt_skema
        )
        return response.json()

    def valider_skema_data(self, skema: dict, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valider data mod skema struktur og returner eventuelle fejl.

        :param skema: Skema prototype eller instans.
        :param data: Dictionary med feltdata til validering.
        :return: Dictionary med feltnavne og tilhørende fejlmeddelelser.
        """
        errors = {}
        
        for item in skema.get("items", []):
            label = item.get("label")
            field_type = item.get("type")
            required = item.get("required", False)
            
            if required and label not in data:
                errors[label] = [f"Feltet '{label}' er påkrævet"]
                continue
                
            if label in data:
                value = data[label]
                field_errors = []
                
                if field_type in ["radioGroup", "dropDown"]:
                    possible_values = item.get("possibleValues", [])
                    if value not in possible_values:
                        field_errors.append(f"Værdi '{value}' er ikke gyldig. Gyldige værdier: {possible_values}")
                        
                elif field_type == "date":
                    if not isinstance(value, str) or len(value) != 10:
                        field_errors.append(f"Ugyldig datoformat. Forventet format: YYYY-MM-DD")
                
                if field_errors:
                    errors[label] = field_errors
                    
        return errors

    def hent_skemareferencer(self, borger: dict) -> List[Dict[str, Any]]:
        """
        Hent og parse alle skema referencer for en borger til en liste af dictionaries.
        
        :param borger: Borger objekt at hente skema referencer for.
        :return: Liste af dictionaries med skema information
        """
        # Tilgå BorgerClient gennem manager hvis tilgængelig, ellers opret direkte
        if self._manager is not None:
            borgere_client = self._manager.borgere
        else:
            # Fallback: opret BorgerClient direkte (ikke anbefalet men funktionelt)
            from kmd_nexus_client.functionality.borgere import BorgerClient
            borgere_client = BorgerClient(self.client)

        visning = borgere_client.hent_visning(borger=borger, visnings_navn="-Alt")
        referencer = borgere_client.hent_referencer(visning=visning)
        
        skemaer = []
        
        # Find alle tokens hvor type er "formDataV2Reference"
        tokens = self._find_all_tokens(referencer, lambda token: 
            isinstance(token, dict) and 
            token.get("type") == "formDataV2Reference"
        )
       
        for token in tokens:
            row = {}
            
            # Grundlæggende felter
            row['Skemaid'] = int(token.get('formDataId', 0))
            row['Navn'] = token.get('name', '')
            
            # Parse dato
            if token.get('date'):
                try:
                    row['Dato'] = datetime.fromisoformat(token['date'].replace('Z', '+00:00'))
                except:
                    row['Dato'] = None
            else:
                row['Dato'] = None
            
            # Status fra workflow state
            if token.get('workflowState') and token['workflowState'].get('name'):
                row['Status'] = token['workflowState']['name']
            else:
                row['Status'] = ''
            
            # Find parent pathway references
            path = self._get_parent_pathway_names(token)
            
            if len(path) >= 2:
                row['Grundforløb'] = path[1]
                row['Forløb'] = path[0]
            else:
                row['Grundforløb'] = ''
                row['Forløb'] = ''
            
            # Håndter _links - bevar den fulde link struktur
            if token.get('_links'):
                row['_links'] = token['_links']
            else:
                row['_links'] = {}
            
            skemaer.append(row)
        
        return skemaer


    # Private/helper methods

    def _find_all_tokens(self, data: Any, condition_func) -> List[Dict]:
        """
        Find alle tokens i nested JSON struktur der opfylder en betingelse.
        
        :param data: JSON data at søge i
        :param condition_func: Function der returnerer True for matchende tokens
        :return: Liste af matchende tokens
        """
        results = []
        
        def search_recursive(obj, parent=None):
            if isinstance(obj, dict):
                # Tilføj parent reference for at kunne navigere op
                obj['_parent'] = parent
                
                if condition_func(obj):
                    results.append(obj)
                
                for key, value in obj.items():
                    if key != '_parent':  # Undgå cirkular reference
                        search_recursive(value, obj)
                        
            elif isinstance(obj, list):
                for item in obj:
                    search_recursive(item, parent)
        
        search_recursive(data)
        return results

    def _get_parent_pathway_names(self, token: Dict) -> List[str]:
        """
        Få parent pathway navne ved at navigere op gennem parent struktur.
        
        :param token: Token at finde parents for
        :return: Liste af pathway navne (nærmeste først)
        """
        path = []
        parent = token.get('_parent')
        
        while parent is not None:
            if (isinstance(parent, dict) and 
                parent.get('type') == 'patientPathwayReference' and 
                parent.get('name')):
                path.append(parent['name'])
            
            parent = parent.get('_parent')
        
        return path
    
    def _find_skematype_by_name(self, skematyper: List[dict], navn: str) -> Optional[dict]:
        """
        Find et skematype i en liste baseret på navn.

        :param skematyper: Liste af skematyper at søge i.
        :param navn: Navn på skematype at finde.
        :return: Skematype hvis fundet, None ellers.
        """
        return next((skematype for skematype in skematyper if skematype.get("title") == navn), None)

    def _find_handling_by_name(self, handlinger: List[dict], navn: str) -> Optional[dict]:
        """
        Find en handling i en liste baseret på navn.

        :param handlinger: Liste af handlinger at søge i.
        :param navn: Navn på handling at finde.
        :return: Handling hvis fundet, None ellers.
        """
        return next((handling for handling in handlinger if handling.get("name") == navn), None)

    def _extract_form_fields(self, skema: dict) -> List[dict]:
        """
        Udtræk form felter fra skema med information om typer og værdier.

        :param skema: Skema instans eller prototype.
        :return: Liste af form felter med metadata.
        """
        fields = []
        for item in skema.get("items", []):
            field_info = {
                "label": item.get("label"),
                "type": item.get("type"),
                "value": item.get("value"),
                "required": item.get("required", False)
            }
            
            if item.get("type") in ["radioGroup", "dropDown"]:
                field_info["possibleValues"] = item.get("possibleValues", [])
                
            fields.append(field_info)
            
        return fields

    def get_field_value(self, skema: dict, field_label: str) -> Any:
        """
        Hent værdi for et specifikt felt i skema.

        :param skema: Skema instans.
        :param field_label: Label for feltet.
        :return: Værdien for feltet eller None hvis ikke fundet.
        """
        for item in skema.get("items", []):
            if item.get("label") == field_label:
                return item.get("value")
        return None

    def set_field_value(self, skema: dict, field_label: str, value: Any) -> bool:
        """
        Sæt værdi for et specifikt felt i skema.

        :param skema: Skema instans eller prototype.
        :param field_label: Label for feltet.
        :param value: Værdi der skal sættes.
        :return: True hvis feltet blev fundet og opdateret, False ellers.
        """
        for item in skema.get("items", []):
            if item.get("label") == field_label:
                item["value"] = value
                return True
        return False
