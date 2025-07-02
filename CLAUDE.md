# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 🚨 KRITISK SIKKERHEDSINSTRUKS FOR KMD NEXUS 🚨

## ABSOLUT PÅKRÆVET SIKKERHEDSPROTOKOL

Du må **ALDRIG** tilgå andre borgere end disse to godkendte test-borgere:
- **Test Borger 1:** CPR `1234567890` (Patient ID: `12345`)
- **Test Borger 2:** CPR `0987654321` (Patient ID: `67890`)

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
citizen = safe_get_citizen(citizens, "1234567890")  # Test Borger 1

# ❌ FORBUDT - brug ALDRIG direkte get_citizen():
# citizen = citizens.get_citizen("1234567890")  # ALDRIG DETTE!
```

### 3. VERIFICÉR TEST-BORGERE
```python
from nexus_ai_safety_wrapper import get_allowed_test_citizens, is_test_citizen

# Se alle godkendte test-borgere:
test_citizens = get_allowed_test_citizens()
for cpr, info in test_citizens.items():
    print(f"{info['name']}: CPR {cpr}")

# Check om CPR er test-borger:
if is_test_citizen("1234567890"):
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

## Project Overview

This is a Python client library for the KMD Nexus API, providing interoperability between Python applications and KMD Nexus using REST API. The client is built around OAuth2 authentication and follows HATEOAS principles for API navigation.

## Development Commands

### Building and Testing
- **Build package**: `uv build`
- **Run tests**: `pytest`
- **Run single test**: `pytest tests/test_filename.py::test_function_name`
- **Install dependencies**: `uv sync`

### Environment Setup
- Copy `env.example` to `.env` and configure with your credentials
- Required environment variables: `CLIENT_ID`, `CLIENT_SECRET`, `INSTANCE`
- Tests load configuration from `.env` file

## Architecture Overview

### Core Components

**NexusClient** (`kmd_nexus_client/client.py`):
- Main client handling OAuth2 authentication and HTTP operations
- Automatically fetches and manages access tokens
- Provides HATEOAS link parsing via `parse_links()` method
- Handles error logging and response validation
- Supports GET, POST, PUT, DELETE with automatic URL normalization

**Functionality Modules** (`kmd_nexus_client/functionality/`):
- **CitizensClient**: Citizen data retrieval and manipulation
- **OrganizationsClient**: Organization and supplier management  
- **AssignmentsClient**: Assignment creation and management
- **GrantsClient**: Grant-related operations
- **CalendarClient**: Calendar and scheduling functionality
- **CasesClient**: Case management operations

### Key Patterns

**Client Initialization Pattern**:
```python
from kmd_nexus_client import NexusClient, CitizensClient

client = NexusClient(instance="instance", client_id="id", client_secret="secret")
citizens = CitizensClient(client)
```

**HATEOAS Navigation**:
- Base client fetches API links during initialization into `client.api` dictionary
- Functionality clients use these links to navigate the API
- Links are automatically normalized to absolute URLs

**Error Handling**:
- All HTTP errors are logged and re-raised via `_handle_errors()`
- Custom validation for missing required API links
- OAuth2 token management is automatic

### Testing Structure

**Test Fixtures** (`tests/fixtures.py`):
- `base_client`: Configured NexusClient instance
- Individual client fixtures for each functionality module
- `test_citizen`: Pre-loaded test citizen data
- All fixtures use session scope where appropriate

**Test Organization**:
- Each functionality module has corresponding test file
- Tests require live API credentials in `env.local`
- Integration tests validate real API responses

### Important Implementation Details

**URL Handling**:
- All URLs are normalized via `_normalize_url()` method
- Supports both relative and absolute URLs
- Base URL constructed from instance name

**Logging**:
- Request/response logging with JSON formatting
- Configurable non-logging endpoints via `_non_logging_endpoints`
- HTTP library logging suppressed to WARNING level

**Data Filtering**:
- `filter_references()` and `filter_pathway_references()` utilities for navigating nested API responses
- Tree traversal with configurable filtering for active pathways only

## Development Notes

- Uses `uv` for dependency management and building
- Python 3.12+ required
- Built with `hatchling` as build backend
- Uses `pytest` for testing with custom fixtures
- Supports both production and development KMD Nexus instances