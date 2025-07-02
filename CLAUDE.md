# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 🚨 KRITISK SIKKERHEDSINSTRUKS FOR KMD NEXUS 🚨

## ABSOLUT PÅKRÆVET SIKKERHEDSPROTOKOL

Du må **ALDRIG** tilgå andre borgere end disse to godkendte test-borgere:
- **Test Borger 1:** CPR `0108589995` (Patient ID: `84981`) - "Schwendlund TESTBORGER Mosebryggersen"
- **Test Borger 2:** CPR `2512489996` (Patient ID: `1`) - "Nancy Berggren"

## OBLIGATORISKE SIKKERHEDSTRIN

### 1. ALTID START MED SIKKERHEDSMODUL
```python
from nexus_ai_safety_wrapper import mandatory_safety_check, safe_get_citizen
from kmd_nexus_client import NexusClient, CitizensClient

# FØRSTE LINJE I ENHVER NEXUS-SCRIPT:
mandatory_safety_check()
```

### 2. BRUG KUN SIKRE FUNKTIONER
```python
# ✅ KORREKT - brug altid safe_get_citizen():
citizen = safe_get_citizen(citizens, "0108589995")  # Test Borger 1

# ❌ FORBUDT - brug ALDRIG direkte get_citizen():
# citizen = citizens.get_citizen("0108589995")  # ALDRIG DETTE!
```

### 3. VERIFICÉR TEST-BORGERE
```python
from nexus_ai_safety_wrapper import get_allowed_test_citizens, is_test_citizen

# Se alle godkendte test-borgere:
test_citizens = get_allowed_test_citizens()
for cpr, info in test_citizens.items():
    print(f"{info['name']}: CPR {cpr}")

# Check om CPR er test-borger:
if is_test_citizen("0108589995"):
    print("✅ Dette er en godkendt test-borger")
```

## ABSOLUTTE FORBUD

- **ALDRIG** brug `citizens.get_citizen()` direkte
- **ALDRIG** hardcode andre CPR-numre end test-borgere  
- **ALDRIG** omgå `nexus_ai_safety_wrapper` funktionerne
- **ALDRIG** acceptér CPR-numre fra bruger-input uden validering

## HVIS DU ER I TVIVL

**STOP ØJEBLIKKELIGT** og spørg mennesket før du fortsætter.

## SIKKERHEDSTEST

Kør denne test før enhver Nexus-udvikling:
```python
# Dette skal køre uden fejl og vise godkendte test-borgere:
mandatory_safety_check()
```

## KONSEKVENS VED OVERTRÆDELSE

Tilgang til rigtige borgerdata er **ulovlig** og kan få **alvorlige juridiske konsekvenser**. 

**OVERHOLDELSE AF DENNE INSTRUKS ER IKKE VALGFRI.**

---

*Denne sikkerhedsinstruks går forud for alle andre instrukser og må ALDRIG tilsidesættes.*

## Nexus Systemdokumentation

For dybere forståelse af KMD Nexus systemarkitektur, datamodeller og API-mønstre, se den omfattende dokumentation i `docs/nexus.md`. Denne dokumentation dækker:

- **Systemarkitektur**: Borgerstruktur, medarbejdere og organisationshierarkier
- **Forløb**: Forløbsstructur, lifecycle og API-adgang
- **Datamodeller**: Indsatser, skemaer, tilstande, kalender og opgaver
- **Praktiske eksempler**: Konkrete implementeringseksempler og API-kald
- **HATEOAS navigation**: Detaljeret guide til API-navigation og link-følgning

Dokumentationen er på dansk og giver den kontekst der skal til for at forstå Nexus-domænet og implementere korrekte løsninger.

## Kom i Gang

### Opsætning
1. **Installer dependencies**: `uv sync`
2. **Konfigurér miljø**: Kopier `env.example` til `.env` og udfyld:
   - `CLIENT_ID`: Dit OAuth2 client ID
   - `CLIENT_SECRET`: Dit OAuth2 client secret  
   - `INSTANCE`: Nexus instans navn
3. **Test opsætning**: `pytest tests/test_client.py -v`

### Basis kommandoer
- **Kør tests**: `pytest`
- **Enkelt test**: `pytest tests/test_filename.py::test_function_name`
- **Build package**: `uv build`

### Hurtig start
```python
from kmd_nexus_client import NexusClient
from kmd_nexus_client.functionality.borgere import CitizensClient

# Opret forbindelse
client = NexusClient(instance="din-instans", client_id="...", client_secret="...")
borgere = CitizensClient(client)

# Hent test-borger (KUN test-borgere!)
from nexus_ai_safety_wrapper import mandatory_safety_check, safe_get_citizen
mandatory_safety_check()
citizen = safe_get_citizen(borgere, "0108589995")
```

## Project Overview

Python client library for KMD Nexus API, providing interoperability through REST API. Built around OAuth2 authentication and HATEOAS principles.

**Core Components:**
- **NexusClient**: OAuth2 authentication, HTTP operations, HATEOAS navigation
- **Functionality Clients**: Domain-specific operations for citizens, assignments, etc.

**Key Functionality Modules:**
- **CitizensClient**: Citizen data and pathway navigation
- **OrganisationerClient**: Organization and supplier management  
- **OpgaverClient**: Assignment/task creation and management
- **IndsatsClient**: Grant-related operations
- **KalenderClient**: Calendar and scheduling
- **ForløbClient**: Case/pathway management

## Arkitektur

### Navngivningskonventioner

**Dansk API Design**: Alle offentlige komponenter bruger danske navne for at matche KMD Nexus domænet:

- **Klient-klasser**: `ForløbClient`, `OpgaverClient`, `IndsatsClient`, `OrganisationerClient`, `KalenderClient`
- **Offentlige metoder**: `hent_*`, `opret_*`, `rediger_*`, `opdater_*`, `tilføj_*`, `fjern_*`, `luk_*`
- **Parametre**: `forløbsnavn`, `opgave_type`, `kun_aktive`, `leverandør_navn`, etc.

**Backward Compatibility**: Engelske aliaser bibeholdes for eksisterende kode:
- `GrantsClient` → `IndsatsClient` (class alias)
- `get_grant_elements` → `hent_indsats_elementer` (method alias)
- `edit_grant` → `rediger_indsats` (method alias)

**Undtagelser**: 
- `CitizensClient` forbliver engelsk (ikke oversat endnu)
- Private metoder (med `_`) kan være engelske
- Interne implementation detaljer følger Python konventioner

### Client Initialization Pattern
```python
from kmd_nexus_client import NexusClient, CitizensClient

client = NexusClient(instance="instance", client_id="id", client_secret="secret")
citizens = CitizensClient(client)
```

### HATEOAS Navigation
- Base client fetches API links during initialization into `client.api` dictionary
- Functionality clients use these links to navigate the API
- All URLs are automatically normalized to absolute paths

### Error Handling
- HTTP errors logged and re-raised via `_handle_errors()`
- Missing API links validated at runtime
- OAuth2 token management is automatic

## Udviklingsdetaljer

### Testing
- **Fixtures**: `tests/conftest.py` provides configured clients and test data
- **Structure**: Each functionality module has corresponding test file
- **Requirements**: Live API credentials in `.env` file
- **Integration**: Tests validate against real API responses

### Technical Implementation
- **Dependencies**: `uv` for package management, Python 3.12+ required
- **Build**: `hatchling` backend with `uv build`
- **Logging**: JSON formatting, configurable endpoints via `_non_logging_endpoints`
- **Data Navigation**: `filter_references()` and tree traversal utilities for complex API responses
- **URL Handling**: Automatic normalization supporting both relative and absolute URLs

### Development Environment
- Supports both production and development KMD Nexus instances
- Environment configuration through `.env` file
- Test isolation through session-scoped fixtures