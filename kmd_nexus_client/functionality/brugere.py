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

    def hent_bruger_ved_navn(self, fuldenavn: str) -> Optional[dict]:
        try:
            encoded_navn = quote(fuldenavn)
            respone = self.client.get(f"{self.client.api["professionals"]}?query={encoded_navn}")
            
            resultater = respone.json()
            
            bruger = next(
                (a for a in resultater if a.get("fullName", "").lower() == fuldenavn.lower()),
                None,
            )
            
            # Faldback: hvis der kun er ét resultat, og alle ord i søgenavnet indgår i fullName
            if bruger is None and len(resultater) == 1:
                ord = fuldenavn.lower().split()
                kandidat_navn = resultater[0].get("fullName", "").lower()
                
                if all(o in kandidat_navn for o in ord):
                    bruger = resultater[0]
            
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
    
    def tilføj_rolle_til_bruger(self, bruger: dict, rollenavn: str) -> bool:
        
        nuværende_roller = self.hent_bruger_roller(bruger)    
        
        # Kontrollere om bruger allerede har rolle
        if nuværende_roller is not None:
            rolle = next(
                (a for a in nuværende_roller if a["name"].lower() == rollenavn.lower()),
                None,
            )
                    
            if rolle is not None:
                return True
        
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
        
        response = self.client.put(konfiguration["_links"]["update"]["href"], konfiguration)
        
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

    def opret_bruger_fra_sts(
        self,
        initialer: str,
        organisation: str,
        signatur: str = "Standard",
        upn_domæne: str = "odense.dk",
    ) -> dict:
        """Opretter en bruger i Nexus ud fra en medarbejder i STS.

        Args:
            initialer: Initialer på medarbejderen der skal oprettes.
            organisation: Tekstbeskrivelse af organisation (medarbejderen tilknyttes ikke en organisation).
            signatur: Navnet på den autosignatur brugeren skal have.
            upn_domæne: Domæne til brugerens UPN og identityId.

        Returns:
            Den oprettede bruger som dict.

        Raises:
            ValueError: Hvis medarbejderen ikke findes i STS, eller signaturen ikke findes.
            HTTPStatusError: Ved øvrige HTTP-fejl.
        """
        try:
            respons = self.client.get(
                f"{self.client.api['importProfessionalFromSts']}?query={quote(initialer)}"
            )
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"{initialer} kunne ikke findes") from e
            raise

        prototype = respons.json()

        signaturer = self.client.get(
            prototype["_links"]["availableProfessionalAutosignatures"]["href"]
        ).json()
        autosignatur = next((s for s in signaturer if s["name"] == signatur), None)

        if autosignatur is None:
            raise ValueError(f"{signatur} kunne ikke findes")

        prototype["initials"] = initialer
        prototype["primaryIdentifier"] = initialer
        prototype["activeDirectoryConfiguration"]["upn"] = f"{initialer}@{upn_domæne}"
        prototype["identityId"] = f"{initialer}@{upn_domæne}"
        # NB: "organizaionName" er bevidst stavet sådan - det er Nexus' eget feltnavn
        prototype["organizaionName"] = organisation
        prototype["departmentName"] = organisation
        prototype["autoSignature"] = autosignatur["id"]

        respons = self.client.post(prototype["_links"]["create"]["href"], prototype)

        return respons.json()

    def opdater_bruger_fra_sts(self, bruger: dict) -> bool:
        """Beder Nexus opdatere en brugers oplysninger fra STS, baseret på brugerens CPR-nummer.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.

        Returns:
            True hvis opdateringen lykkedes, False hvis brugeren ikke har et gyldigt CPR-nummer.
        """
        konfiguration = self.hent_bruger_konfiguration(bruger)

        try:
            cpr = sanitize_cpr(konfiguration.get("cpr") or "")
        except ValueError:
            return False

        response = self.client.put(
            self.client.api["stsLinkUpdates"], {"type": "cpr", "identifier": cpr}
        )

        return response.status_code == 200

    def opdater_profil(
        self,
        bruger: dict,
        stilling: Optional[str] = None,
        primær_organisation: Optional[str] = None,
        standard_leverandør: Optional[str] = None,
        medcom_lokationsnummer: Optional[int] = None,
        aktiv: Optional[bool] = None,
        autorisationskode: Optional[str] = None,
    ) -> bool:
        """Opdaterer en brugers konfiguration. Kun parametre der er angivet (ikke None) ændres.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.
            stilling: Navn på stilling.
            primær_organisation: Navn på brugerens primære organisation.
            standard_leverandør: Navn på standardleverandør på arbejdstider.
            medcom_lokationsnummer: Id på standard MedCom-afsender. 0 fjerner afsenderen.
            aktiv: Om brugeren er aktiv.
            autorisationskode: Brugerens autorisationskode.

        Returns:
            True hvis konfigurationen blev opdateret.

        Raises:
            ValueError: Hvis en angiven stilling, organisation eller leverandør ikke findes.
        """
        konfiguration = self.hent_bruger_konfiguration(bruger)
        links = konfiguration["_links"]

        def find(link: str, navn: str) -> dict:
            muligheder = self.client.get(links[link]["href"]).json()
            fundet = next((m for m in muligheder if m["name"] == navn), None)
            if fundet is None:
                raise ValueError(f"'{navn}' kunne ikke findes")
            return fundet

        if stilling is not None:
            konfiguration["professionalJob"] = find("availableProfessionalJobs", stilling)

        if primær_organisation is not None:
            konfiguration["primaryOrganization"] = find("organizations", primær_organisation)

        if standard_leverandør is not None:
            konfiguration["defaultOrganizationSupplier"] = find(
                "availableOrganizationSuppliers", standard_leverandør
            )

        if medcom_lokationsnummer is not None:
            if medcom_lokationsnummer != 0:
                konfiguration["defaultMedcomSenderOrganizationId"] = medcom_lokationsnummer
                konfiguration["replyToDefaultMedcomSenderOrganization"] = True
            else:
                konfiguration["defaultMedcomSenderOrganizationId"] = None
                konfiguration["replyToDefaultMedcomSenderOrganization"] = False

        if autorisationskode is not None:
            if konfiguration.get("authorizationCodeConfiguration") is None:
                konfiguration["authorizationCodeConfiguration"] = {}
            konfiguration["authorizationCodeConfiguration"]["authorizationCode"] = autorisationskode

        if aktiv is not None:
            konfiguration["active"] = aktiv

        response = self.client.put(links["update"]["href"], konfiguration)

        return response.status_code == 200

    def opdater_national_rolle(self, bruger: dict, national_rolle: str) -> bool:
        """Sætter en brugers nationale rolle.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.
            national_rolle: "SUND_ASSIST_R1" eller "SUND_ASSIST_R2".

        Returns:
            True hvis rollen blev sat.

        Raises:
            ValueError: Hvis rollen er ugyldig.
        """
        if national_rolle not in ("SUND_ASSIST_R1", "SUND_ASSIST_R2"):
            raise ValueError("Ugyldig rolle")

        konfiguration = self.hent_bruger_konfiguration(bruger)
        konfiguration["nationalRoleConfiguration"] = {
            "nationalRole": national_rolle,
            "_links": {},
        }

        response = self.client.put(konfiguration["_links"]["update"]["href"], konfiguration)

        return response.status_code == 200

    def opdater_outlook_synkronisering(self, bruger: dict, send_til_exchange: bool) -> bool:
        """Slår overførsel af kalenderbegivenheder til Exchange/Outlook til eller fra.

        Args:
            bruger: Bruger-dict eller medarbejder som returneret af `hent_bruger` eller 'hent_medarbejder'.
            send_til_exchange: Om kalenderbegivenheder skal overføres til Exchange/Outlook.

        Returns:
            True hvis konfigurationen blev opdateret.
        """
        konfiguration = self.hent_bruger_konfiguration(bruger)
        konfiguration["exchangeConfiguration"]["sendToExchange"] = send_til_exchange

        response = self.client.put(konfiguration["_links"]["update"]["href"], konfiguration)

        return response.status_code == 200

    def opdater_brugerprofil(
        self,
        bruger: dict,
        organisation: Optional[str] = None,
        autosignatur_id: Optional[int] = None,
    ) -> bool:
        """Opdaterer en brugers organisationstekst og/eller autosignatur.

        Args:
            bruger: Bruger-dict som returneret af `hent_bruger`.
            organisation: Ny tekstbeskrivelse af organisation. Tom/None lader den være uændret.
            autosignatur_id: Id på ny autosignatur. None eller 0 lader den være uændret.

        Returns:
            True hvis brugeren blev opdateret.
        """
        if "update" not in bruger["_links"]:
            bruger = self.client.get(bruger["_links"]["self"]["href"]).json()
        else:
            bruger = dict(bruger)

        if autosignatur_id:
            bruger["autosignatureId"] = autosignatur_id

        if organisation:
            bruger["organizationName"] = organisation

        response = self.client.put(bruger["_links"]["update"]["href"], bruger)

        return response.status_code == 200
