"""User Profile Service - Defect: Unsafe nested dictionary access causing KeyError / TypeError."""

from typing import Dict, Any, Optional


def extract_user_zipcode(user_payload: Optional[Dict[str, Any]]) -> str:
    """Extracts zip code from user payload."""
    # DEFECT 1 (Null Dereference): Direct nested key access without checking if 'profile', 'address', or user_payload is None
    # Crashes with TypeError if user_payload is None, or KeyError if 'profile'/'address'/'zipcode' is missing!
    return user_payload["profile"]["address"]["zipcode"]


def format_full_name(user_data: Dict[str, Any]) -> str:
    """Formats full name from first and last name keys."""
    # DEFECT 2 (Missing Validation): Assumes keys always exist and non-null
    # Raises TypeError when first_name or last_name is None, or KeyError if key absent
    first = user_data["first_name"]
    last = user_data["last_name"]
    return f"{first.capitalize()} {last.capitalize()}"


def check_applicant_age(user_data: Dict[str, Any]) -> bool:
    """Checks if applicant is 18 years or older."""
    # DEFECT 3 (Type Mismatch / Coercion Error): Compares string age directly to integer without int() conversion
    # Raises TypeError: '>' not supported between instances of 'str' and 'int' if age is passed as string ("25")
    age = user_data.get("age")
    return age >= 18
