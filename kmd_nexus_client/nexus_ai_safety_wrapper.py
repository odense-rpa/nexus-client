"""
KMD Nexus AI Safety Wrapper
===========================

KRITISK SIKKERHEDSMODUL: Beskytter mod utilsigtet adgang til rigtige borgere.

Dette modul SKAL bruges af AI-systemer når de arbejder med KMD Nexus API'et.
Modulet tillader kun adgang til foruddefinerede test-borgere.

ALDRIG omgå disse sikkerhedsfunktioner!
"""

import logging
from typing import Optional, Union

# =============================================================================
# GODKENDTE TEST-BORGERE (DE ENESTE TILLADTE)
# =============================================================================

ALLOWED_TEST_CITIZENS = {
    "0108589995": {
        "patient_id": 84981,
        "name": "Schwendlund TESTBORGER Mosebryggersen",
        "description": "Primær test-borger til AI-udvikling"
    },
    "2512489996": {
        "patient_id": 1, 
        "name": "Nancy Berggren",
        "description": "Sekundær test-borger til AI-udvikling"
    }
}

ALLOWED_TEST_CPRS = list(ALLOWED_TEST_CITIZENS.keys())
ALLOWED_TEST_PATIENT_IDS = [citizen["patient_id"] for citizen in ALLOWED_TEST_CITIZENS.values()]

# =============================================================================
# SIKKERHEDSKLASSER
# =============================================================================

class NexusSecurityError(Exception):
    """
    Kritisk sikkerhedsfejl: Forsøg på at tilgå ikke-godkendt borger.
    
    Denne exception kastes når AI-systemet forsøger at tilgå borgere
    der ikke er på listen over godkendte test-borgere.
    """
    pass


class NexusSecurityViolation(Exception):
    """
    Alvorlig sikkerhedskrænkelse: Forsøg på at omgå sikkerhedssystem.
    """
    pass

# =============================================================================
# SIKKERHEDSFUNKTIONER
# =============================================================================

def validate_citizen_access(cpr: Optional[str] = None, patient_id: Optional[int] = None) -> bool:
    """
    Validerer at kun godkendte test-borgere tilgås.
    
    Args:
        cpr: CPR-nummer der skal valideres
        patient_id: Patient ID der skal valideres
        
    Returns:
        True hvis adgang er tilladt
        
    Raises:
        NexusSecurityError: Hvis ikke-godkendt borger forsøges tilgået
        NexusSecurityViolation: Hvis ingen parametre gives
    """
    
    if not cpr and not patient_id:
        raise NexusSecurityViolation(
            "SIKKERHEDSKRÆNKELSE: validate_citizen_access() kaldt uden parametre. "
            "Dette kan være et forsøg på at omgå sikkerhed."
        )
    
    if cpr:
        if cpr not in ALLOWED_TEST_CPRS:
            raise NexusSecurityError(
                f"🚨 ADGANG NÆGTET 🚨\n"
                f"CPR '{cpr}' er IKKE en godkendt test-borger!\n"
                f"Godkendte test-borgere:\n"
                + "\n".join([
                    f"  - {test_cpr}: {info['name']}" 
                    for test_cpr, info in ALLOWED_TEST_CITIZENS.items()
                ])
            )
        
        citizen_info = ALLOWED_TEST_CITIZENS[cpr]
        print(f"✅ Adgang godkendt til: {citizen_info['name']} (CPR: {cpr})")
    
    if patient_id:
        if patient_id not in ALLOWED_TEST_PATIENT_IDS:
            raise NexusSecurityError(
                f"🚨 ADGANG NÆGTET 🚨\n"
                f"Patient ID '{patient_id}' er IKKE en godkendt test-borger!\n"
                f"Godkendte Patient IDs: {ALLOWED_TEST_PATIENT_IDS}"
            )
        
        # Find borger info baseret på patient_id
        for cpr, info in ALLOWED_TEST_CITIZENS.items():
            if info["patient_id"] == patient_id:
                print(f"✅ Adgang godkendt til: {info['name']} (Patient ID: {patient_id})")
                break
    
    return True


def mandatory_safety_check() -> bool:
    """
    OBLIGATORISK sikkerhedstest der SKAL køres før enhver Nexus-operation.
    
    Tester at sikkerhedssystemet fungerer korrekt og kan blokere
    ulovlige adgangsforsøg.
    
    Returns:
        True hvis alle sikkerhedstests bestås
        
    Raises:
        SystemError: Hvis sikkerhedssystem ikke fungerer korrekt
    """
    
    print("🔒 NEXUS AI SIKKERHEDSTEST - STARTER...")
    print("=" * 50)
    
    # Test 1: Verificer at whitelist blokerer ugyldige CPR-numre
    print("Test 1: Verificerer whitelist-beskyttelse...")
    try:
        validate_citizen_access(cpr="9999999999")  # Skal fejle
        raise SystemError(
            "💥 KRITISK SIKKERHEDSFEJL 💥\n"
            "Whitelist blokerer IKKE ugyldige CPR-numre!\n"
            "STOP AL UDVIKLING - sikkerhedssystem er defekt!"
        )
    except NexusSecurityError:
        print("✅ Whitelist blokerer korrekt ugyldige CPR-numre")
    
    # Test 2: Verificer at whitelist blokerer ugyldige Patient IDs
    print("Test 2: Verificerer Patient ID beskyttelse...")
    try:
        validate_citizen_access(patient_id=99999)  # Skal fejle
        raise SystemError(
            "💥 KRITISK SIKKERHEDSFEJL 💥\n"
            "Whitelist blokerer IKKE ugyldige Patient IDs!\n"
            "STOP AL UDVIKLING - sikkerhedssystem er defekt!"
        )
    except NexusSecurityError:
        print("✅ Whitelist blokerer korrekt ugyldige Patient IDs")
    
    # Test 3: Verificer at godkendte test-borgere kan tilgås
    print("Test 3: Verificerer adgang til test-borgere...")
    for test_cpr, info in ALLOWED_TEST_CITIZENS.items():
        validate_citizen_access(cpr=test_cpr)
        validate_citizen_access(patient_id=info["patient_id"])
    
    print("=" * 50)
    print("🔒 SIKKERHEDSTEST BESTÅET ✅")
    print(f"Godkendte test-borgere:")
    for cpr, info in ALLOWED_TEST_CITIZENS.items():
        print(f"  - {info['name']}: CPR {cpr} (Patient ID: {info['patient_id']})")
    print("=" * 50)
    print("🟢 NEXUS AI-UDVIKLING KAN FORSÆTTE SIKKERT")
    
    return True


def safe_get_citizen(citizens_client, cpr: str):
    """
    Sikker wrapper til citizens.get_citizen() der validerer adgang først.
    
    Args:
        citizens_client: CitizensClient instance
        cpr: CPR-nummer på test-borger
        
    Returns:
        Borger-objekt fra Nexus API
        
    Raises:
        NexusSecurityError: Hvis CPR ikke er godkendt test-borger
    """
    
    # OBLIGATORISK sikkerhedscheck
    validate_citizen_access(cpr=cpr)
    
    # Log sikker adgang
    citizen_info = ALLOWED_TEST_CITIZENS[cpr]
    print(f"🔐 Sikker API-kald: Henter {citizen_info['name']} (CPR: {cpr})")
    
    # Kald det faktiske API
    return citizens_client.get_citizen(cpr)


def get_allowed_test_citizens() -> dict:
    """
    Returnerer information om alle godkendte test-borgere.
    
    Returns:
        Dictionary med test-borger information
    """
    return ALLOWED_TEST_CITIZENS.copy()


def is_test_citizen(cpr: str) -> bool:
    """
    Checker om et CPR-nummer tilhører en godkendt test-borger.
    
    Args:
        cpr: CPR-nummer der skal checkes
        
    Returns:
        True hvis CPR er en godkendt test-borger, False ellers
    """
    return cpr in ALLOWED_TEST_CPRS


def log_security_event(event_type: str, details: str) -> None:
    """
    Logger sikkerhedsrelaterede events for audit-trail.
    
    Args:
        event_type: Type af sikkerhedsevent
        details: Detaljer om eventet
    """
    
    logging.warning(f"NEXUS_SECURITY_{event_type}: {details}")


# =============================================================================
# MODUL INITIALISERING
# =============================================================================

def _module_init():
    """Initialiserer sikkerhedsmodul ved import."""
    
   
    # Log at sikkerhedsmodul er aktiveret
    log_security_event(
        "MODULE_LOADED", 
        f"Nexus AI Safety Wrapper aktiveret. Godkendte borgere: {len(ALLOWED_TEST_CITIZENS)}"
    )


# Automatisk initialisering ved import
_module_init()


# =============================================================================
# EKSPORT AF OFFENTLIGE FUNKTIONER
# =============================================================================

__all__ = [
    'mandatory_safety_check',
    'validate_citizen_access', 
    'safe_get_citizen',
    'get_allowed_test_citizens',
    'is_test_citizen',
    'NexusSecurityError',
    'NexusSecurityViolation',
    'ALLOWED_TEST_CPRS',
    'ALLOWED_TEST_PATIENT_IDS'
]