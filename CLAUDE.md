# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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