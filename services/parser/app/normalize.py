import re
from email_validator import validate_email, EmailNotValidError
import phonenumbers


def normalize_email(addr: str | None) -> str:
    if not addr:
        return ""
    try:
        v = validate_email(addr, allow_smtputf8=True)
        return v.email.lower()
    except EmailNotValidError:
        return ""


def normalize_phone(phone: str | None, default_region: str = "US") -> str:
    if not phone:
        return ""
    # Remove all but digits and plus
    cleaned = re.sub(r"[^0-9+]+", "", phone)
    try:
        num = phonenumbers.parse(cleaned, default_region)
        if phonenumbers.is_valid_number(num):
            return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
        return ""
    except Exception:
        return ""


def normalize_name(name: str | None) -> str:
    if not name:
        return ""
    # Simple canonicalization
    name = re.sub(r"\s+", " ", name).strip()
    return name

