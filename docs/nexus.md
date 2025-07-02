# KMD Nexus - Udviklingsdokumentation

## Introduktion

KMD Nexus er en samlet platform til borgerforløb, der understøtter digital samarbejde på tværs af sundhed, omsorg og socialområdet gennem faglige metoder i social- og sundhedssektoren. Systemet sikrer konsistens og datadrevet styring på tværs af sundhedsområdet, velfærd og sociale services.

## Indholdsfortegnelse

1. [Teknisk Oversigt](#teknisk-oversigt)
   - [API Adgang](#api-adgang)
   - [API Endpoints og Anvendelse](#api-endpoints-og-anvendelse)
   - [Fejlhåndtering og Datatyper](#fejlhåndtering-og-datatyper)

2. [Systemarkitektur](#systemarkitektur)
   - [Borgerstruktur i Nexus](#borgerstruktur-i-nexus)
   - [Medarbejderstruktur](#medarbejderstruktur)
   - [Organisationshierarki](#organisationshierarki)

3. [Forløb](#forløb)
   - [Forløbsstruktur og Navigation](#forløbsstruktur-og-navigation)
   - [Forløbs Lifecycle](#forløbs-lifecycle)
   - [API-adgang til Forløb](#api-adgang-til-forløb)

4. [MedCom](#medcom)
   - [MedCom Indbakke Navigation](#medcom-indbakke-navigation)
   - [MedCom Besked Struktur](#medcom-besked-struktur)
   - [MedCom Lifecycle](#medcom-lifecycle)

5. [Indsatser](#indsatser)

6. [Skemaer](#skemaer)

7. [Tilstande](#tilstande)

8. [Kalender](#kalender)

9. [Opgaver](#opgaver)

10. [Aktivitetslister](#aktivitetslister)

## Teknisk Oversigt

### API Adgang

KMD Nexus tilbyder API-adgang gennem OAuth2 Client Credentials flow og følger HATEOAS (Hypermedia as the Engine of Application State) princippet for API-design.

#### Endpoints

**Autentificering:**
```
https://iam.nexus.kmd.dk/authx/realms/{instance}/protocol/openid-connect/token
```

**Base API URL:**
```
https://{instance}.nexus.kmd.dk/api/core/mobile/{instance}/v2/
```

Hvor `{instance}` er din lokale Nexus-instans (f.eks. `odensekommune`).

#### OAuth2 Client Credentials

Systemet anvender OAuth2 Client Credentials grant type til autentificering, hvilket er velegnet til server-til-server kommunikation hvor der ikke er behov for brugerinteraktion.

#### HATEOAS Principper

API'et følger HATEOAS-arkitekturen, hvilket betyder at API-responser indeholder links til relaterede ressourcer og handlinger, der gør det muligt for klienter at navigere gennem API'et dynamisk uden forudgående kendskab til URL-strukturer.

### API Endpoints og Anvendelse

#### NexusClient Struktur

Nexus API'et tilgås gennem `NexusClient` som håndterer OAuth2 autentificering og kommunikation. Klienten parser automatisk HATEOAS-links fra root API'et og gemmer dem i `client.api` dictionary.

**Client initialisering:**
```python
from kmd_nexus_client import NexusClient

client = NexusClient(
    instance="odensekommune", 
    client_id="<client_id>", 
    client_secret="<client_secret>"
)

# API endpoints tilgængelige via client.api dictionary
print(client.api)  # Viser alle tilgængelige endpoints
```

**URL-struktur:**
- **Token URL:** `https://iam.nexus.kmd.dk/authx/realms/{instance}/protocol/openid-connect/token`
- **Base API URL:** `https://{instance}.nexus.kmd.dk/api/core/mobile/{instance}/v2/`

#### Borger (Patient) Endpoints

Nexus anvender internt betegnelsen "patient" i API'et. `CitizensClient` tilbyder en række metoder til at arbejde med borgerdata:

**Hent borger via CPR:**
```python
from kmd_nexus_client import CitizensClient

citizens = CitizensClient(client)
citizen = citizens.get_citizen("1234567890")  # CPR automatisk sanitized
```

**API-kald:** `POST patientDetailsSearch` med payload:
```json
{
  "businessKey": "1234567890",
  "keyType": "CPR"
}
```

**Borger forløb og aktiviteter:**
```python
# Hent borger præferencer
preferences = citizens.get_citizen_preferences(citizen)

# Hent specifikt forløb (default: "- Alt")
pathway = citizens.get_citizen_pathway(citizen, pathway_name="- Alt")

# Hent forløbsreferencer
references = citizens.get_citizen_pathway_references(pathway)

# Hent forløbsaktiviteter  
activities = citizens.get_citizen_pathway_activities(pathway)

# Løs en reference til fuldt objekt
full_object = citizens.resolve_reference(reference)

# Hent udlån
lendings = citizens.get_citizen_lendings(citizen)
```

#### HATEOAS Navigation

API'et bruger `_links` objekter til navigation mellem ressourcer:
```python
# Links findes i alle response objekter under "_links"
citizen_links = citizen["_links"]
preferences_url = citizen_links["patientPreferences"]["href"]

# Client kan navigere til relaterede ressourcer
response = client.get(preferences_url)
```

### Fejlhåndtering og Datatyper

#### HTTP Status Codes

Nexus API'et anvender standard HTTP statuskoder for fejlrapportering:

- **200 OK** - Succesfuld anmodning
- **401 Unauthorized** - Ugyldig eller udløbet autentificering
- **404 Not Found** - Ressource findes ikke eller er ikke tilgængelig
- **500 Internal Server Error** - Server fejl

Python-klienten håndterer automatisk fejl via `HTTPStatusError` exceptions:

```python
from httpx import HTTPStatusError

try:
    citizen = citizens.get_citizen("1234567890")
    if citizen is None:
        print("Borger ikke fundet eller ikke tilgængelig")
except HTTPStatusError as e:
    if e.response.status_code == 401:
        print("Autentificering fejlede")
    elif e.response.status_code == 404:
        print("Endpoint ikke fundet")
    else:
        print(f"API fejl: {e.response.status_code}")
```

#### Datatyper og ID-formater

**ID-formater:**
- Nexus anvender `int` datatype til alle ID'er
- ID-felter er generelt navngivet `id`
- Eksempel: `{"id": 12345, "name": "Forløb A"}`

**CPR-håndtering:**
- CPR-numre sanitizes automatisk af klienten via `sanitize_cpr()` funktionen
- Input: `"12 34 56 - 78 90"` → Output: `"1234567890"`

## Systemarkitektur

### Borgerstruktur i Nexus

KMD Nexus organiserer borgerdata i en hierarkisk struktur med klart definerede relationer mellem forskellige komponenter.

#### Datamodel vs. Visninger (Views)

**Vigtig skelnen:**
- **Datamodellen** beskriver hvordan data faktisk er organiseret i systemet
- **Visninger (Views)** er foruddefinerede JSON-baserede præsentationer af datastrukturen

Visninger fungerer som database views - de strukturerer og filtrerer den underliggende datamodel til specifikke formål uden at ændre på selve datastrukturen.

#### Reference-hierarki (Pathways)

Nexus har et hierarkisk mellemlag kaldet **"referencer"** (ofte omtalt som "pathways" i API'et) mellem borgeren og de faktiske forløb, indsatser og skemaer.

**Vigtig arkitektonisk begrænsning:**
Du kan **ikke direkte hente** hele reference-træet fra API'et. I stedet skal du:

1. Tilgå borgerens præferencer (`CITIZEN_PREFERENCES`)
2. Vælge en specifik visning (f.eks. "- Alt")  
3. Hente reference-træet gennem denne visning

```python
# IKKE muligt: client.get("/citizen/12345/references")  ❌

# Korrekt tilgang gennem visninger: ✅
preferences = citizens.get_citizen_preferences(citizen)
alt_view = citizens.get_citizen_pathway(citizen, pathway_name="- Alt")
references = citizens.get_citizen_pathway_references(alt_view)
```

**Reference-træ struktur:**
```
Borger
└── Citizen Preferences
    ├── Visning "- Alt"
    │   └── Reference-træ (pathways)
    │       ├── Reference til Grundforløb 1
    │       │   ├── Reference til Underforløb 1.1
    │       │   │   ├── Reference til Indsats A
    │       │   │   └── Reference til Skema B
    │       │   └── Reference til Underforløb 1.2
    │       └── Reference til Tilstand X
    └── Visning "Aktive forløb"
        └── Filtreret reference-træ
```

Dette design betyder at Nexus **kontrollerer adgangen** til data gennem foruddefinerede visninger i stedet for at tillade fri navigation i datastrukturen.

#### Citizen Preferences og Visninger

Borgere har tilknyttet forskellige visninger gennem deres `citizen_preferences`. Hver visning præsenterer borgerdata i en specifik hierarkisk struktur.

**Eksempel på visning "- Alt":**
```json
[
  {
    "obj1": "...",
    "children": [
      {"obj1.1": "..."},
      {"obj1.2": "..."}
    ]
  },
  {"obj2": "..."}
]
```

**Tilgang til visninger:**
```python
preferences = citizens.get_citizen_preferences(citizen)
alt_view = citizens.get_citizen_pathway(citizen, pathway_name="- Alt")
```

Visningen "- Alt" giver typisk en komplet oversigt over borgerens forløb, tilstande og tilknyttede elementer organiseret hierarkisk.

**To hovedkomponenter i borgervisninger:**

1. **PathwayReferences** - Hierarkisk forløbsstruktur
2. **PatientActivities** - Flad liste med øvrige borgerelementer

```python
# Hent hierarkisk forløbsstruktur
references = citizens.get_citizen_pathway_references(alt_view)

# Hent flad liste med aktiviteter (tilstande, organisationer, medicinkort osv.)
activities = client.get(alt_view["_links"]["patientActivities"]["href"]).json()
```

#### PathwayReferences vs. PatientActivities

**PathwayReferences:**
- Hierarkisk struktur: Grundforløb → Forløb → elementer (indsatser, skemaer)
- Indeholder **referencer** der skal løses via `referencedObject`
- Kan filtreres (f.eks. `active_pathways_only`)

**PatientActivities:**
- Flad liste uden hierarki
- Indeholder elementer der ikke tilhører forløb: tilstande, organisationer, medicinkort
- Indeholder **direkte objekter** med `self` links (ikke referencer)
- Ingen pagination eller filtrering
- **Vigtigt:** PatientActivities er ofte "halve objekter" - man bør kalde `self` linket for at få komplette data

```python
# Behandl patientActivities korrekt
for activity in activities:
    # Hent fuldt objekt via self link
    full_object = client.get(activity["_links"]["self"]["href"]).json()
    
    # Brug full_object i stedet for activity
    print(f"Fuld aktivitet: {full_object}")
```

**Dataoverlap:**
Der er overlap mellem de to strukturer og direkte API-kald. F.eks.:
- Tilstande kan findes både i `patientActivities` og via `citizen["_links"]["patientConditions"]`
- Det handler om hvilken "vej" man vælger til data

#### Referenser vs. Faktiske Objekter

**Vigtigt princip:** Visninger indeholder **referencer** til objekter, ikke objekterne selv.

Når man navigerer gennem en visning, får man reference-objekter der:
- Indeholder basale metadata (navn, type, status)
- Har `_links` med URL til det faktiske objekt
- Kan have forskellige tilgængelige funktioner afhængigt af objekttype

**Løsning af referencer:**
```python
# Få reference fra visning
references = citizens.get_citizen_pathway_references(pathway)
reference = references[0]  # F.eks. en forløbsreference

# Løs reference til fuldt objekt
full_object = citizens.resolve_reference(reference)

# Eller manuelt via _links
if "referencedObject" in reference["_links"]:
    full_object = client.get(reference["_links"]["referencedObject"]["href"]).json()
```

#### Forløbsstruktur
Nexus anvender en to-lags forløbsstruktur:

- **Grundforløb** (øverste niveau)
  - **Underforløb** (andet og nederste niveau)

En borger kan have flere grundforløb, og hvert grundforløb kan indeholde flere underforløb.

#### Borgerkomponenter

**Tilstande:**
- En borger kan have et antal tilstande tilknyttet
- Tilstande er ikke forløbsspecifikke

**Organisationstilknytning:**
- En borger kan tilknyttes flere organisationer (mange-til-mange relation)
- En organisation kan have mange borgere tilknyttet
- Organisationer er struktureret i et klassisk hierarki

**Indsatser & Skemaer:**
- Placeres altid under et specifikt forløb (enten grundforløb eller underforløb)
- Kan ikke eksistere løsrevet fra forløbsstrukturen

**Dokumenter:**
- PDF-dokumenter og andre filer kan uploades til specifikke forløb
- Dokumenter er primært PDF-filer, men andre filtyper understøttes

**MedCom Integration:**
- Hver borger har en MedCom-indbakke
- MedCom-beskeder kan tilknyttes specifikke forløb
- Beskeder kan også eksistere uden forløbstilknytning

**Kalender:**
- Hver borger har sin egen kalender
- Indeholder begivenheder som i en klassisk kalender
- Eksisterer på samme hierarkiske niveau som MedCom-indbakken

**Opgaver:**
- Opgaver kan tilknyttes forskellige elementer i systemet
- Fungerer som et tværgående koordinationsværktøj
- *Se dedikeret [Opgaver](#opgaver) sektion for detaljer*

#### Underliggende Datamodel

**Vigtig note:** Den følgende struktur repræsenterer brugerens **mentale model** af hvordan data er organiseret. I virkeligheden ligger alle forløb, indsatser og skemaer bag det hierarkiske reference-system (pathways) beskrevet ovenfor.

Den opfattede dataorganisation i Nexus ser sådan ud:

```
Borger (brugerens mentale model)
├── Grundforløb 1                    ← Tilgås via reference
│   ├── Underforløb 1.1              ← Tilgås via reference
│   │   ├── Indsatser                ← Tilgås via reference
│   │   │   └── [Opgave]
│   │   ├── Skemaer                  ← Tilgås via reference
│   │   │   └── [Opgave]
│   │   └── Dokumenter (PDF/andre filer)
│   └── Underforløb 1.2              ← Tilgås via reference
│       ├── Indsatser                ← Tilgås via reference
│       ├── Skemaer                  ← Tilgås via reference
│       └── Dokumenter (PDF/andre filer)
├── Grundforløb 2                    ← Tilgås via reference
│   └── Underforløb 2.1              ← Tilgås via reference
│       └── Dokumenter (PDF/andre filer)
├── Tilstande (globale)              ← Tilgås via reference
│   └── [Opgave]
├── Organisationer (mange-til-mange)
│   ├── Organisation A
│   ├── Organisation B
│   └── Organisation C
├── Medarbejdere (mange-til-mange med organisationer)
│   ├── Medarbejder 1 (rolle A, rolle B)
│   ├── Medarbejder 2 (ingen roller)
│   └── Medarbejder 3 (rolle C)
├── Kalender
│   ├── Begivenhed 1
│   ├── Begivenhed 2
│   └── Begivenhed 3
└── MedCom Indbakke
    ├── MedCom Besked 1 (tilknyttet forløb)
    │   └── [Opgave]
    └── MedCom Besked 2 (ikke tilknyttet)
        └── [Opgave]
```

### Medarbejderstruktur

Medarbejdere i Nexus har deres egen struktur med fleksible tilknytninger til organisationer og roller.

#### Medarbejder-Organisation Relation

Medarbejdere og organisationer har en **mange-til-mange relation**:
- En medarbejder kan være tilknyttet flere organisationer
- En organisation kan have mange medarbejdere
- Denne struktur tillader fleksible arbejdsarrangementer på tværs af organisatoriske grænser

#### Rollesystem

Medarbejdere kan tildeles **0 til mange roller**:
- En medarbejder kan arbejde uden specifikke roller tildelt
- En medarbejder kan have flere forskellige roller samtidigt
- Roller definerer typisk adgangsrettigheder og funktionaliteter

```
Medarbejder
├── Organisation A (tilknytning)
├── Organisation B (tilknytning)
├── Rolle 1 (tildelt)
├── Rolle 2 (tildelt)
└── Rolle N (tildelt)
```

#### Integration med Opgavesystem

Medarbejdere kan tildeles som **ansvarlig medarbejder** på opgaver, hvilket skaber en direkte kobling mellem medarbejdere og arbejdsprocesser i systemet.

### Organisationshierarki

Organisationer i Nexus følger en hierarkisk struktur, hvor organisationer kan have over- og underordnede enheder:

```
Kommune/Region
├── Forvaltning A
│   ├── Afdeling A1
│   │   ├── Team A1.1
│   │   └── Team A1.2
│   └── Afdeling A2
├── Forvaltning B
│   └── Afdeling B1
└── Forvaltning C
```

Denne organisationsstruktur gør det muligt at:
- Delegere ansvar og adgang på forskellige niveauer
- Organisere borgerforløb efter organisatorisk tilhørsforhold
- Sikre korrekt dataadgang baseret på organisationstilknytning

# KMD Nexus - Udviklingsdokumentation (Del 2)

*Fortsættelse fra Del 1...*

## Forløb

Forløb er centrale i Nexus og repræsenterer strukturerede behandlings- eller omsorgsforløb som borgere kan tilmeldes. Forløb organiseres hierarkisk og har en komplet lifecycle fra oprettelse til lukning.

### Forløbsstruktur og Navigation

#### Forløbshierarki

Forløb i Nexus følger en hierarkisk struktur:

```
Patient
└── availablePathwayAssociation (Grundforløb)
    └── availableNestedProgramPathways (Specifikke forløb)
        └── Konkret forløb (f.eks. "Demensforløb")
```

#### Oprettelse af Nye Forløb

```python
# 1. Hent tilgængelige grundforløb
grundforløb_list = client.get(citizen["_links"]["availablePathwayAssociation"]["href"]).json()

# 2. Find specifikt grundforløb
sundhedsfagligt_grundforløb = None
for grundforløb in grundforløb_list:
    if grundforløb["name"] == "Sundhedsfagligt grundforløb":
        sundhedsfagligt_grundforløb = grundforløb
        break

# 3. Hent nested forløbsmuligheder
nested_pathways = client.get(sundhedsfagligt_grundforløb["_links"]["availableNestedProgramPathways"]["href"]).json()

# 4. Find specifikt forløb med filtrering
demensforløb = None
for pathway in nested_pathways:
    if pathway["name"] == "Demensforløb" and pathway.get("active") == 1:
        demensforløb = pathway
        break
```

#### Navigation af Eksisterende Forløb

**Metode 1: Via activePrograms (nem, men uden reference)**
```python
# Hent aktive forløb direkte
active_programs = client.get(citizen["_links"]["activePrograms"]["href"]).json()

for program in active_programs:
    if program["name"] == "Demensforløb":
        # Du har forløbet, men ikke pathway reference
        pathway_object = program
        break
```

**Metode 2: Via visninger (giver pathway reference)**
```python
# Hent "-Alt" visning og pathway references
alt_view = citizens.get_citizen_pathway(citizen, pathway_name="- Alt")
references = citizens.get_citizen_pathway_references(alt_view)

def find_pathway_reference(references, target_name, active_only=True):
    """Rekursiv søgning efter forløbsreference"""
    for ref in references:
        # Check om dette er den ønskede forløbsreference
        if (ref.get("type") == "patientPathwayReference" and 
            ref.get("name") == target_name):
            if not active_only or ref.get("pathwayStatus") == "ACTIVE":
                return ref
        
        # Søg rekursivt i children
        if "children" in ref:
            found = find_pathway_reference(ref["children"], target_name, active_only)
            if found:
                return found
    return None

# Find Demensforløb reference
demens_ref = find_pathway_reference(references, "Demensforløb")
if demens_ref:
    # Nu har du pathway referencen - kan løse til fuldt objekt
    full_pathway = citizens.resolve_reference(demens_ref)
```

### Pathway Reference vs. Forløbsobjekt

**Vigtig skelnen:** Der er forskel mellem en **pathway reference** (fra visninger som "-Alt") og det **faktiske forløbsobjekt**.

#### Pathway Reference Struktur (fra visninger)

```json
{
  "type": "patientPathwayReference",
  "id": null,
  "version": 0,
  "name": "Demensforløb",
  "date": "2024-03-18T11:53:12.000+0000",
  "children": [],
  "pathwayStatus": "ACTIVE",
  "patientPathwayId": 609142,
  "programPathwayId": 58,
  "pathwayTypeId": 22,
  "parentPathwayId": null,
  "_links": {
    "referencedObject": {"href": "..."},
    "self": {"href": "..."}
  }
}
```

**Vigtige felter i pathway reference:**
- **patientPathwayId:** Unikt ID for den patient-specifikke forløbsinstans
- **programPathwayId:** Reference til forløbstemplate/program
- **pathwayTypeId:** Forløbstype klassifikation
- **pathwayStatus:** "ACTIVE" eller andre statusser
- **children:** Array af underforløb/child-objekter
- **date:** Oprettelsesdato i ISO format

#### Faktisk Forløbsobjekt

For at få det faktiske forløbsobjekt skal man løse referencen:

```python
# Fra pathway reference til faktisk forløbsobjekt
pathway_reference = demens_ref  # Fra visning
full_pathway = client.get(pathway_reference["_links"]["referencedObject"]["href"]).json()

# Eller via resolve_reference helper
full_pathway = citizens.resolve_reference(pathway_reference)
```

Det faktiske forløbsobjekt indeholder flere links og detaljer:

```json
{
  "id": 609142,
  "name": "Demensforløb",
  "pathwayStatus": "ACTIVE",
  "_links": {
    "self": {"href": "..."},
    "close": {"href": "..."},
    "unclosableReferences": {"href": "..."},
    "pathwayReferences": {"href": "..."},
    "patientActivities": {"href": "..."},
    "availableFormDefinitions": {"href": "..."},
    "documentPrototype": {"href": "..."},
    "availableProfessionals": {"href": "..."},
    "availableOrganisations": {"href": "..."}
  }
}
```

*Note: Komplet eksempel på faktisk forløbsobjekt struktur vil blive tilføjet når tilgængeligt.*

### Forløbs Lifecycle

#### 1. Forløbsoprettelse (Enrollment)

```python
# Tilmeld patient til forløb via enroll link
response = client.put(demensforløb["_links"]["enroll"]["href"], json="")

# Verificer oprettelse
new_pathway = response.json()
if new_pathway["pathwayStatus"] == "ACTIVE":
    print(f"Forløb oprettet: {new_pathway['name']}")
```

**Vigtige punkter:**
- Enrollment bruges PUT metode med tom JSON string som body
- Response returnerer komplet forløbsobjekt med alle links
- Check `pathwayStatus = "ACTIVE"` for at verificere succesfuld oprettelse

#### 2. Arbejde med Eksisterende Forløb

```python
# Via pathway reference (fra visning)
pathway_ref = find_pathway_reference(references, "Demensforløb")
if pathway_ref:
    # Løs til faktisk forløbsobjekt
    pathway_data = citizens.resolve_reference(pathway_ref)
else:
    # Via activePrograms (direkte objekt)
    active_programs = client.get(citizen["_links"]["activePrograms"]["href"]).json()
    pathway_data = next((p for p in active_programs if p["name"] == "Demensforløb"), None)

# Tilgå relaterede objekter (kræver faktisk forløbsobjekt)
if pathway_data and "_links" in pathway_data:
    references = client.get(pathway_data["_links"]["pathwayReferences"]["href"]).json()
    activities = client.get(pathway_data["_links"]["patientActivities"]["href"]).json()
    available_forms = client.get(pathway_data["_links"]["availableFormDefinitions"]["href"]).json()
```

#### 3. Forløbslukning

```python
# Check om forløb kan lukkes
unclosable = client.get(pathway_data["_links"]["unclosableReferences"]["href"]).json()

if len(unclosable) == 0:
    # Forløb kan lukkes
    response = client.put(pathway_data["_links"]["close"]["href"], json={})
    if response.status_code == 200:
        print("Forløb lukket succesfuldt")
else:
    print(f"Forløb kan ikke lukkes - {len(unclosable)} blokerende referencer")
```

**Luknings-workflow:**
1. **Check blokering:** Hent `unclosableReferences` for at se om andre objekter blokerer lukning
2. **Evaluér count:** Hvis count > 0, kan forløb ikke lukkes
3. **Luk forløb:** Hvis count = 0, kald `close` endpoint med PUT og tom JSON body
4. **Verificér:** Status 200 indikerer succesfuld lukning

### API-adgang til Forløb

#### Direkte Endpoints

```python
# Hent alle aktive forløb for en patient
active_pathways = client.get(f"patients/{citizen_id}/programs/active").json()

# Hent specifikt forløb
specific_pathway = client.get(f"patientPathways/{pathway_id}").json()

# Hent self-reference til forløb
self_ref = client.get(f"patientPathways/{pathway_id}/selfReference").json()
```

#### Filtrering og Søgning

Forløb kan filtreres på forskellige parametre:
- `?active=true` - Kun aktive forløb
- `[name]='Forløbsnavn'` - Filter på navn
- `[type]='patientPathwayReference'` - Filter på type

#### Integration med Øvrige Objekter

Forløb fungerer som udgangspunkt for adgang til relaterede objekter:

```python
# Fra forløb til skemaer
available_forms = client.get(pathway["_links"]["availableFormDefinitions"]["href"]).json()

# Fra forløb til dokumenter
doc_prototype = client.get(pathway["_links"]["documentPrototype"]["href"]).json()

# Fra forløb til henvisninger
references = client.get(pathway["_links"]["pathwayReferences"]["href"]).json()

# Fra forløb til aktiviteter
activities = client.get(pathway["_links"]["patientActivities"]["href"]).json()

# Fra forløb til medarbejdere
professionals = client.get(pathway["_links"]["availableProfessionals"]["href"]).json()

# Fra forløb til organisationer
organisations = client.get(pathway["_links"]["availableOrganisations"]["href"]).json()
```

## MedCom

MedCom beskeder er en central del af kommunikation i Nexus og følger danske standarder for elektronisk kommunikation i sundhedssektoren.

### MedCom Indbakke Navigation

MedCom beskeder tilgås gennem borgerens indbakke med en pagineret struktur der kræver flere trin for at nå de faktiske beskeder.

#### Grundlæggende Navigation

```python
# 1. Hent indbakke fra borger
inbox = client.get(citizen["_links"]["inboxMessages"]["href"]).json()

print(f"Total beskeder: {inbox['totalItems']}")

# 2. Gå gennem alle sider
for page in inbox["pages"]:
    # Hent indhold af hver side
    page_content = client.get(page["_links"]["self"]["href"]).json()
    
    # 3. Gå gennem besked-referencer på siden
    for message_ref in page_content:
        # Hent fuld besked fra reference
        full_message = client.get(message_ref["_links"]["self"]["href"]).json()
        
        print(f"Besked: {full_message.get('subject', 'Ingen emne')}")
```

#### Pagineret Struktur

```json
{
  "totalItems": 5,
  "pages": [
    {
      "_links": {
        "self": {"href": "https://..."}
      }
    }
  ]
}
```

**Tre-trins proces:**
1. **Indbakke** → får pagination info og side-links
2. **Sider** → får besked-referencer 
3. **Besked-referencer** → får fulde besked-objekter

### MedCom Besked Struktur

#### Komplet Besked Objekt

```json
{
  "_links": {
    "self": {"href": "https://..."},
    "accept": {"href": "https://..."},
    "archive": {"href": "https://..."}
  },
  "raw": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0i...",
  "subject": "Besked emne",
  "pathwayAssociation": {
    "_links": {
      "availablePathwayAssociation": {"href": "https://..."}
    },
    "placement": {
      "programPathwayId": "pathway-id",
      "name": "Pathway Name"
    }
  }
}
```

#### Vigtige Felter

- **raw:** Base64 encoded MedCom XML indhold (dekodes med standard Base64 decoder)
- **subject:** Beskedens emne
- **pathwayAssociation:** Forløbstilknytning og tilgængelige forløb
- **_links:** Handlinger der kan udføres på beskeden

#### Vigtige Links

- **self:** Hent/opdater besked
- **accept:** Accepter besked (markerer som læst/behandlet)
- **archive:** Arkiver besked

### MedCom Lifecycle

MedCom beskeder går gennem en defineret lifecycle med specifikke API-operationer.

#### 1. Modtaget Besked

```python
# Besked findes i indbakke (allerede vist ovenfor)
# Status: Ubehandlet/ny besked
```

#### 2. Accepter Besked

```python
# Accepter besked (markerer som læst/behandlet)
response = client.put(
    full_message["_links"]["accept"]["href"], 
    json=full_message  # Send original besked som body
)

if response.status_code == 200:
    print("Besked accepteret")
```

#### 3. Tildel til Forløb (valgfrit)

```python
# Modificer besked for at tildele til specifikt forløb
modified_message = full_message.copy()
modified_message["pathwayAssociation"]["placement"] = {
    "programPathwayId": "target-pathway-id",
    "name": "MedCom"
}

# Opdater besked med forløbstilknytning
response = client.put(
    full_message["_links"]["self"]["href"],
    json=modified_message
)
```

#### 4. Arkiver Besked

```python
# Arkiver besked (fjerner fra aktiv indbakke)
response = client.post(
    full_message["_links"]["archive"]["href"],
    json=full_message  # Send original besked som body
)

if response.status_code == 200:
    print("Besked arkiveret")
```

#### Forløbsintegration

```python
# Hent tilgængelige forløb
available_pathways = client.get(
    full_message["pathwayAssociation"]["_links"]["availablePathwayAssociation"]["href"]
).json()

# Find specifikt forløb
target_pathway = None
for pathway in available_pathways:
    if pathway["name"] == "MedCom":  # Eller specifik pathway
        target_pathway = pathway
        break

# Tildel besked til fundet forløb
if target_pathway:
    modified_message = full_message.copy()
    modified_message["pathwayAssociation"]["placement"] = {
        "programPathwayId": target_pathway["programPathwayId"],
        "name": "MedCom"
    }
    
    # Gem ændringer
    response = client.put(
        full_message["_links"]["self"]["href"],
        json=modified_message
    )
```

## Indsatser

### Leverandørstruktur

Indsatser i Nexus leveres af leverandører, som har deres egen uafhængige hierarkiske struktur. Det er vigtigt at forstå at leverandørtræet er **helt uafhængigt af organisationstræet**.

**Vigtig skelnen:**
- **Organisationer:** Håndterer ansvar, adgang og koordination
- **Leverandører:** Leverer konkrete indsatser til borgere
- **Relation:** Leverandører og organisationer har ikke nødvendigvis 1:1 forhold

En leverandør kan levere indsatser på tværs af forskellige organisationer, og en organisation kan arbejde med flere forskellige leverandører.

```
Leverandørhierarki (uafhængigt af organisationer):
Leverandør A
├── Afdeling A1
│   ├── Team A1.1
│   └── Team A1.2
└── Afdeling A2

Leverandør B
├── Afdeling B1
└── Afdeling B2
```

### Lovgrundlag for Indsatser

Hver indsats kan bevilliges på baggrund af specifikke lovparagraffer. Nexus understøtter forskellige lovgivninger:

**Understøttede love:**
- **SEL** - Serviceloven
- **SUL** - Sundhedsloven  
- **ÆL** - Ældreloven
- *Yderligere lovgivninger vil blive tilføjet løbende*

Paragrafferne sikrer at indsatser er korrekt hjemlet juridisk og gør det muligt at spore lovgrundlaget for bevillingen.

*API-detaljer for indsatser vil blive implementeret og dokumenteret af Claude Code.*

## Skemaer

Skemaer i Nexus implementerer digitale versioner af papirskemaer. Systemadministratorer definerer skematyper med forskellige felttyper, og brugere opretter konkrete skemainstanser baseret på disse definitioner.

### Skematyper vs. Skemainstanser

**Skematype (Template):**
- Definition af felter, felttyper og struktur
- Oprettes af systemadministrator
- Eksempel: "Observation" skematype

**Skemainstans:**
- Konkret udfyldt skema baseret på en skematype
- Indeholder brugerdata og gemmes revisioneret
- Tilgås via referencer som andre objekter

### API-adgang til Skemaer

#### Hentning af Skemainstans

```python
# Via reference fra borgervisning
schema_reference = # ... fundet i pathway references
schema_instance = citizens.resolve_reference(schema_reference)

# Eller direkte via referencedObject link
schema_instance = client.get(schema_reference["_links"]["referencedObject"]["href"]).json()
```

#### Tilgængelige Skematyper

```python
# Via forløbsreference
pathway_ref = # ... specifik forløbsreference
available_forms = client.get(pathway_ref["_links"]["availableFormDefinitions"]["href"]).json()

# Eller via borger (alle tilgængelige skematyper)
available_forms = client.get(citizen["_links"]["availableFormDefinitions"]["href"]).json()
```

### Skemastruktur og Felter

Skemaer indeholder et `items` array med alle felter:

```python
# Behandl skemafelter
for item in schema_instance["items"]:
    label = item["label"]
    field_type = item.get("type")
    
    if field_type in ["radioGroup", "dropDown"]:
        # Dropdown/radio felter
        possible_values = item["possibleValues"]
        selected_value = item.get("value")
        
    elif label == "Diagnose":
        # Specielt diagnosefelt (kræver diagnose JSON)
        diagnosis_data = item.get("value")  # Kompleks JSON struktur
        
    else:
        # Almindelige felter (tekst, dato, osv.)
        field_value = item.get("value")
```

**Felttyper:**
- **Tekstfelter** - værdi i `value`
- **Datofelter** - værdi i `value` 
- **Dropdown/RadioGroup** - valgmuligheder i `possibleValues`, valgt værdi i `value`
- **Diagnosefelt** - speciel JSON struktur i `value`

*Denne liste er ikke komplet. Generelt følger **simple felttyper** samme mønster som tekst- og datofelter, mens **komplekse felttyper** typisk kræver JSON objekter i `value` feltet.*

### Revisionshistorik

```python
# Hent historik for et skema
audit_data = client.get(schema_instance["_links"]["audit"]["href"]).json()
```

### Skemastatus

Skemaer har status som indikerer deres tilstand:
- **Udfyldt** - skema er færdigudfyldt
- **Låst** - skema kan ikke længere redigeres
- *Yderligere statusser kan findes i systemet*

### Oprettelse af Skemaer

Oprettelse af et nyt skema følger en 5-trins proces:

#### 1. Hent Skemadefinition og Vælg Handling

```python
# Via forløb (skema oprettes på dette forløb)
form_definitions = client.get(pathway_ref["_links"]["availableFormDefinitions"]["href"]).json()

# Eller via borger (skema oprettes direkte på borgeren)  
form_definitions = client.get(citizen["_links"]["availableFormDefinitions"]["href"]).json()

# Find ønsket skemadefinition
target_definition = None
for definition in form_definitions:
    if definition["name"] == "Observation":  # Eksempel: Observation skematype
        target_definition = definition
        break

action_name = "Aktivt"  # Navn på handling der skal udføres
```

#### 2. Hent Prototype Objekt

```python
# Hent prototype via formdataPrototype link
prototype = client.get(target_definition["_links"]["formdataPrototype"]["href"]).json()
```

#### 3. Find Tilgængelig Action

```python
# Hent availableActions via _links
available_actions = client.get(prototype["_links"]["availableActions"]["href"]).json()

# Find den ønskede action
target_action = None
for action in available_actions:
    if action["name"] == action_name:
        target_action = action
        break
```

#### 4. Udfyld Prototype Items

```python
# Udfyld skemafelter baseret på felttyper
for item in prototype["items"]:
    if item["label"] == "Patientens navn":
        item["value"] = "John Doe"
    elif item["label"] == "Dato" and item["type"] == "date":
        item["value"] = "2025-01-15"
    elif item["type"] == "dropDown":
        # Vælg fra possibleValues
        item["value"] = item["possibleValues"][0]  # Vælg første mulighed
```

#### 5. Opret Skema

```python
# POST den udfyldte prototype til createFormData
response = client.post(
    target_action["_links"]["createFormData"]["href"], 
    json=prototype
)

new_schema = response.json()
```

# KMD Nexus - Udviklingsdokumentation (Del 3)

*Fortsættelse fra Del 2...*

## Tilstande (Patient Conditions)

Tilstande beskriver en borgers aktuelle helbredsmæssige eller funktionelle tilstand. De er **forskellige fra diagnoser** og fungerer som en beskrivelse af borgerens nuværende situation.

### Typer af Tilstande

Fagligt findes der to kategorier af tilstande:
- **Helbredstilstande** - beskriver borgerens helbredsmæssige status
- **Funktionsevnetilstande** - beskriver borgerens funktionelle kapaciteter

Begge typer implementeres som `patientCondition` i Nexus API'et.

### Globale vs. Forløbsspecifikke

Tilstande er **globale** for borgeren og ikke knyttet til specifikke forløb, i modsætning til indsatser og skemaer.

### API-adgang til Tilstande

#### Hentning af Borgerens Tilstande

```python
# Hent alle tilstande for en borger
conditions = client.get(citizen["_links"]["patientConditions"]["href"]).json()

# Behandl tilstande
for condition in conditions:
    print(f"Tilstand: {condition.get('name')}, Status: {condition.get('state')}")
```

### Oprettelse af Tilstande

Oprettelse af en tilstand følger et lignende mønster som skemaer:

#### 1. Hent Tilgængelige Tilstandstyper

```python
# Hent tilgængelige tilstandsklassifikationer
condition_types = client.get(citizen["_links"]["availableConditionClassification"]["href"]).json()

# Find ønsket tilstandstype
target_condition_type = None
for condition_type in condition_types:
    if condition_type["name"] == "Gå på toilet":  # Eksempel: funktionsevnetilstand
        target_condition_type = condition_type
        break
    # Andre eksempler: "Bevægeapparat" (helbredstilstand)
```

#### 2. Hent Tilstandsprototype

```python
# Hent prototype for tilstandstypen
prototype = client.get(target_condition_type["_links"]["conditionPrototype"]["href"]).json()
```

#### 3. Udfyld Tilstandsstatus

```python
# Sæt tilstandens status ud fra mulige værdier
possible_states = prototype["state"]["possibleValues"]
prototype["state"] = possible_states[0]  # Vælg første mulige tilstand

# Andre felter kan også udfyldes efter behov
```

#### 4. Opret Tilstand

```python
# POST prototypen til create-linket
response = client.post(
    prototype["_links"]["create"]["href"],
    json=prototype
)

new_condition = response.json()
```

*Tilstandstyper kommer fra det kommunale Fællessprog 3 (FSIII) klassifikationssystem.*

## Kalender

Hver borger har sin egen **personlige kalender** kaldet "Borgerkalender" som kan tilgås gennem borgerens præferencer.

### Borgerkalender

#### API-adgang til borgerkalender

```python
# Hent borgerens præferencer
preferences = citizens.get_citizen_preferences(citizen)

# Find kalendre under CITIZEN_CALENDAR feltet
calendars = preferences.get("CITIZEN_CALENDAR", [])

# Find den primære borgerkalender
borger_calendar = None
for calendar in calendars:
    if calendar.get("name") == "Borgerkalender":
        borger_calendar = calendar
        break

if borger_calendar:
    # Tilgå kalenderdata via _links
    calendar_data = client.get(borger_calendar["_links"]["self"]["href"]).json()
    
    # Hent kalenderbegivenheder for en periode
    events_url = calendar_data["_links"]["events"]["href"]
    
    # Parametre for tidsperiode (Zulu tid format)
    params = {
        "from": "2025-01-01T00:00:00Z",    # Start dato
        "to": "2025-01-31T23:59:59Z"       # Slut dato
    }
    
    # Hent begivenheder for perioden
    events = client.get(events_url, params=params).json()
    
    # Behandl begivenheder
    for event in events:
        print(f"Begivenhed: {event.get('title')}, Dato: {event.get('start')}")
```

**Vigtige punkter:**
- `CITIZEN_CALENDAR` feltet kan indeholde **flere kalendre**
- Borgerens **primære kalender** har altid `name='Borgerkalender'`
- Kalenderadgang følger samme HATEOAS-mønster som andre ressourcer

**Kalenderbegivenheder:**
- Tilgås via `events` link i kalenderdata
- Kræver `from` og `to` parametre i JSON datoformat (Zulu tid)
- Returnerer begivenheder for den specificerede tidsperiode

## Opgaver

Opgaver fungerer som et **tværgående koordinationsværktøj** i Nexus der gør det muligt at spore og tildele ansvar for specifikke handlinger på tværs af forskellige systemelementer.

### Opgavetilknytning

Opgaver kan tilknyttes til alle hovedtyper af elementer i systemet:
- **MedCom-beskeder** - opfølgning på beskeder
- **Indsatser** - opgaver relateret til leverance af indsatser  
- **Skemaer** - udfyldelse eller gennemgang af skemaer
- **Tilstande** - opfølgning på borgerens tilstande

Dette gør opgaver til et **systemovergribende** koordinationsværktøj der kan bruges uanset hvor i borgerens forløb man befinder sig.

### Opgaveegenskaber

Hver opgave indeholder følgende information:

- **title:** Overskrift/titel på opgaven
- **description:** Detaljeret beskrivelse af opgavens indhold  
- **startDate + startTime:** Hvornår opgaven starter (dato og tid)
- **dueDate + dueTime:** Forfaldsdato og -tid - hvornår opgaven skal være færdig (valgfrit)
- **organizationAssignee:** Ansvarlig organisation (objekt med organizationId og displayName)
- **professionalAssignee:** Specifik medarbejder med ansvar (valgfrit)

### Integration i Systemstrukturen

Opgaver er integreret på tværs af hele Nexus-arkitekturen:

```
Systemintegration af opgaver:
├── Borgerforløb
│   ├── Indsatser → [Opgave]
│   └── Skemaer → [Opgave]
├── Globale elementer
│   ├── Tilstande → [Opgave]
│   └── MedCom beskeder → [Opgave]
└── Tværgående visning
    └── Aktivitetslister (kan vise opgaver fra alle kilder)
```

**Vigtigt for systemforståelse:** Opgaver skaber sammenhæng mellem organisationer (ansvar), medarbejdere (udførelse) og borgerelementer (kontekst), hvilket gør dem centrale for koordination i systemet.

### API-adgang til Opgaver

#### Hentning af Eksisterende Opgaver

Hvis et objekt (skema, tilstand, indsats osv.) understøtter opgaver, findes opgave-links i objektets `_links`:

```python
# Hent aktive opgaver for et objekt
if "activeAssignments" in some_object["_links"]:
    active_tasks = client.get(some_object["_links"]["activeAssignments"]["href"]).json()
    
    for task in active_tasks:
        print(f"Opgave: {task['title']}, Forfald: {task['dueDate']} {task['dueTime']}")
```

#### Oprettelse af Opgaver

Opgaveoprettelse følger samme mønster som skemaer:

```python
# 1. Hent tilgængelige opgavetyper
available_types = client.get(some_object["_links"]["availableAssignmentTypes"]["href"]).json()

# 2. Find ønsket opgavetype og hent prototype
target_type = None
for assignment_type in available_types:
    if assignment_type["name"] == "Opfølgning med resultat":  # Realistisk opgavetype
        target_type = assignment_type
        break

prototype = client.get(target_type["_links"]["assignmentPrototype"]["href"]).json()

# 3. Find tilgængelige actions på prototypen
actions = prototype["actions"]  # Actions objekt direkte på prototype

# 4. Udfyld prototype felter
prototype["title"] = "Kontakt borger vedr. medicin"
prototype["description"] = "Ring til borger for at følge op på medicintilstand"
prototype["startDate"] = "2025-01-15"
prototype["startTime"] = "09:00:00"
# Forfaldsdato er valgfrit
prototype["dueDate"] = "2025-02-01"  # Valgfrit
prototype["dueTime"] = "12:00:00"    # Valgfrit

# Tildel ansvarlig organisation (normalt påkrævet)
prototype["organizationAssignee"] = {
    "organizationId": 12345,
    "displayName": "Sundhedsplejen Odense"
}

# Medarbejder er valgfrit
# prototype["professionalAssignee"] = {...}  # Hvis relevant

# 5. Opret opgave via passende action
create_action = actions.get("create")  # Eller specifik action navn
response = client.post(create_action["_links"]["self"]["href"], json=prototype)
new_task = response.json()
```

#### Håndtering af Eksisterende Opgaver

```python
# Hent opgave og tilgængelige handlinger
task = active_tasks[0]  # En specifik opgave
task_actions = task["actions"]

# Afslut opgave
if "Afslut" in task_actions:
    response = client.post(task_actions["Afslut"]["_links"]["self"]["href"], json=task)
    
# Rediger opgave (andre actions kan være tilgængelige)
if "Rediger" in task_actions:
    # Opdater felter og post tilbage
    task["description"] = "Opdateret beskrivelse"
    response = client.post(task_actions["Rediger"]["_links"]["self"]["href"], json=task)
```

**Vigtige principper:**
- Opgaver tilknyttes via `activeAssignments` og `availableAssignmentTypes` links
- Oprettelse følger prototype → actions mønster som andre objekter
- Eksisterende opgaver har `actions` objekt til lukning og redigering
- "Afslut" action er standard for at lukke opgaver

## Aktivitetslister

Aktivitetslister er **separate visninger** der giver tværgående overblik over data på tværs af borgere og organisationer. Disse administreres af systemadministratorer og tildeles specifikke brugere eller roller.

### Formål og Anvendelse

Aktivitetslister bruges til at vise:
- Lister over MedCom beskeder 
- Åbne opgaver
- Indsatser
- Andre tværgående data

**Eksempler på anvendelse:**
- Alle borgere tilknyttet et bestemt plejehjem
- Alle borgere med en specifik opgavetype på tværs af organisationer
- Åbne opgaver for en specifik medarbejder
- MedCom beskeder modtaget i dag

### Adgangskontrol

**Rettighedstildeling:**
- Aktivitetslister kan tildeles til **individuelle medarbejdere**
- Aktivitetslister kan tildeles til **roller** (alle medarbejdere med denne rolle får adgang)

**API-adgang:**
```python
# Hent medarbejderens preferences (IKKE borgerens preferences)
user_preferences = client.get(client.api["preferences"]).json()

# Find aktivitetslister under ACTIVITY_LIST feltet
activity_lists = user_preferences.get("ACTIVITY_LIST", [])

for activity_list in activity_lists:
    list_data = client.get(activity_list["_links"]["self"]["href"]).json()
```

### Filtrering og Fleksibilitet

Aktivitetslister kan filtreres på:
- **Organisation** - begræns til specifikke organisationsenheder
- **Medarbejder** - vis kun data relevant for bestemte medarbejdere

### Hentning af Aktivitetslisteindhold

For at få det faktiske indhold af en aktivitetsliste skal man hente `content` med eventuelle filtreringsparametre:

```python
# Hent content med filtrering og pagination
activity_list = activity_lists[0]  # En specifik aktivitetsliste fra preferences

# Hent content via _links fra aktivitetslisten
content_url = activity_list["_links"]["content"]["href"]

# Parametre for filtrering og pagination
params = {
    "pageSize": 50,                                      # Antal elementer per side
    "assignmentOrganizationAssignee": 12345,             # Valgfrit: filter på organisation ID (default: ALL_ORGANIZATIONS)
    "assignmentProfessionalAssignee": 67890              # Valgfrit: filter på medarbejder ID (default: NO_PROFESSIONAL_CRITERIA)
}

# Hent sidestruktur
pages_response = client.get(content_url, params=params).json()

# Response er et JSON array med sideobjekter
for page in pages_response:
    # Hent indholdet af hver side via content-link
    page_content = client.get(page["_links"]["content"]["href"]).json()
    
    # Behandl sideindhold (array af aktiviteter/opgaver/beskeder)
    for item in page_content:
        print(f"Element: {item['name']}, Type: {item['type']}")
```

**Pagination-struktur:**
1. Hent content URL via aktivitetslistens `_links["content"]["href"]`
2. Kald content URL med filtre og `pageSize`
3. Få JSON array med sideobjekter  
4. Hent faktisk indhold via hver sides `_links["content"]["href"]`

### Relation til Borgere

Selvom aktivitetslister ikke er direkte tilknyttet borgere, indeholder de elementer der **tilhører specifikke borgere**:
- Opgaver med reference til den borger de vedrører
- Indsatser knyttet til bestemte borgerforløb  
- MedCom beskeder sendt til/fra specifikke borgere

Dette giver et tværgående perspektiv mens der stadig er sporbarhed tilbage til den oprindelige borger.

