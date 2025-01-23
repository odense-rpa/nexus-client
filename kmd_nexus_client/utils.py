from datetime import datetime
from typing import Callable

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

def sanitize_cpr(cpr: str) -> str:
    """
    Sanitize a CPR number by removing any spaces or dashes.
    
    :param cpr: A CPR number to sanitize.
    :return: The sanitized CPR number.
    """
    cpr = cpr.replace("-", "").replace(" ", "").strip()
    
    if not is_valid_cpr(cpr):
        raise ValueError("Invalid CPR number.")
    
    return cpr


def visitor(element: dict, callback: Callable , child_key: str = "children") -> dict:
    """
    Visit each element in a nested dictionary.

    :param element: The dictionary to visit.
    :param callback: The function to call for each element.
    :param child_key: The key to use for child elements.
    :return: The modified dictionary.
    """
    if child_key in element:
        for child in element[child_key]:
            visitor(child, callback, child_key)
    
    callback(element)
    
    return element