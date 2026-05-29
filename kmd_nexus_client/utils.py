"""
CPR (Danish Social Security Number) validation and sanitization utilities.

This module provides utilities for working with Danish CPR numbers,
including validation and cleaning functionality.
"""

from datetime import datetime


def is_valid_cpr(cpr: str) -> bool:
    """
    Validate a Danish CPR number.

    :param cpr: A CPR number to validate.
    :return: True if the CPR number is valid, False otherwise.
    """
    if not cpr:
        return False

    # CPR numbers must be 10 characters long
    if len(cpr) != 10:
        return False

    # CPR numbers must be numeric
    if not cpr.isnumeric():
        return False

    # CPR numbers must have a valid date
    try:
        datetime.strptime(cpr[:6], "%d%m%y")
    except ValueError:
        return False

    # CPR numbers no longer have a valid checksum, so no check is done
    return True


def sanitize_citizen_identifier(identifier: str) -> str:
    """
    Sanitize a CPR-like citizen identifier by removing any spaces or dashes.

    Nexus test data may expose anonymous exact identifiers that have the same
    10-digit shape as CPR numbers without being valid civil registration dates.
    Lookup code should still be able to search those exact identifiers.

    :param identifier: A CPR-like citizen identifier to sanitize.
    :return: The sanitized identifier.
    """
    identifier = identifier.replace("-", "").replace(" ", "").strip()

    if len(identifier) != 10 or not identifier.isnumeric():
        raise ValueError("Invalid citizen identifier.")

    return identifier


def sanitize_cpr(cpr: str) -> str:
    """
    Sanitize and validate a real CPR number.

    Use :func:`sanitize_citizen_identifier` for exact lookup of Nexus test
    citizens that may use anonymous non-date identifiers.
    """
    try:
        cpr = sanitize_citizen_identifier(cpr)
    except ValueError as error:
        raise ValueError("Invalid CPR number.") from error
    if not is_valid_cpr(cpr):
        raise ValueError("Invalid CPR number.")
    return cpr


def normalize_name(value: str | None) -> str:
    """
    Normalize human-facing Nexus names for stable comparisons.

    :param value: Name to normalize.
    :return: Case-folded name with repeated whitespace collapsed.
    """
    if value is None:
        return ""
    return " ".join(value.casefold().split())
