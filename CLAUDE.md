# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
   - `HOST`: Nexus host segment, f.eks. `nexus` eller `nexus-test`
3. **Test opsætning**: `pytest tests/test_client.py -v`

### Basis kommandoer
- **Kør tests**: `pytest`
- **Enkelt test**: `pytest tests/test_filename.py::test_function_name`
- **Build package**: `uv build`

### Hurtig start
```python
from kmd_nexus_client.manager import NexusClientManager

# Opret forbindelse (anbefalet måde)
nexus = NexusClientManager(
    instance="din-instans",
    client_id="...",
    client_secret="...",
    host="nexus",
)

# Hent test-borger
citizen = nexus.borgere.hent_borger("0108589995")

# Arbejd med referencer - nem adgang via manager
resolved = nexus.hent_fra_reference(reference)

# Adgang til alle klienter via manager
indsatser = nexus.indsatser.hent_indsats_referencer(citizen)
opgaver = nexus.opgaver.hent_opgaver(resolved_object)
```

## Project Overview

Python client library for KMD Nexus API, providing interoperability through REST API. Built around OAuth2 authentication and HATEOAS principles.

**Core Components:**
- **NexusClientManager**: Facade providing unified access to all functionality (anbefalet)
- **NexusClient**: OAuth2 authentication, HTTP operations, HATEOAS navigation
- **Functionality Clients**: Domain-specific operations accessed via manager

**Key Functionality Modules (adgang via NexusClientManager):**
- **BorgerClient** (`nexus.borgere`): Citizen data and pathway navigation
- **OrganisationerClient** (`nexus.organisationer`): Organization and supplier management  
- **OpgaverClient** (`nexus.opgaver`): Assignment/task creation and management
- **IndsatsClient** (`nexus.indsatser`): Grant-related operations
- **KalenderClient** (`nexus.kalender`): Calendar and scheduling
- **ForløbClient** (`nexus.forløb`): Case/pathway management

**Manager Benefits:**
- **Enkel referenceopløsning**: `nexus.hent_fra_reference(reference)` i stedet for `client.nexus_client.hent_fra_reference(reference)`
- **Konsistent adgang**: Alle klienter tilgås via samme manager
- **Lazy loading**: Klienter instantieres kun når de bruges

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

client = NexusClient(
    instance="instance",
    client_id="id",
    client_secret="secret",
    host="nexus",
)
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
