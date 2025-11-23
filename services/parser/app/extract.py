import re
from typing import List, Dict


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:(?:\+\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4})")


def extract_contacts_freeform(text: str) -> List[Dict[str, str]]:
    """Heuristic extraction from free text. Multiple contacts may be present.
    Strategy:
      - Find candidate blocks separated by blank lines or lines starting with cues (name/title/company/email/phone)
      - Extract email + phone from each block
      - Guess name/title/company from common patterns
    """
    contacts: List[Dict[str, str]] = []

    # Split into blocks by two or more newlines to capture signature-like chunks
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        b = block.strip()
        if not b:
            continue

        emails = EMAIL_RE.findall(b)
        phones = PHONE_RE.findall(b)

        # Name/Title/Company cues
        name = _extract_first_match(b, [
            r"^\s*(?:best,\s*)?([A-Z][A-Za-z\-\'\s]{1,60})\s*$",
            r"^\s*([A-Z][A-Za-z\-\'\s]{1,60}),?\s*(?:CEO|CTO|CFO|COO|VP|Director|Manager|Head|Lead)\b",
            r"^\s*Name\s*[:\-]\s*(.+)$",
        ])

        title = _extract_first_match(b, [
            r"\b(CEO|CTO|CFO|COO|VP(?:\s+of\s+\w+)?|Director(?:\s+of\s+\w+)?|Manager|Head|Lead|Principal|Founder|Owner)\b",
            r"^\s*Title\s*[:\-]\s*(.+)$",
        ])

        company = _extract_first_match(b, [
            r"^\s*Company\s*[:\-]\s*(.+)$",
            r"\b(?:at|@)\s+([A-Z][\w&\-\'\s]{1,80})\b",
        ])

        # If we found at least one email or phone, consider it a contact block
        if emails or phones or name or title or company:
            contacts.append({
                "name": name or "",
                "title": title or "",
                "company": company or "",
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else "",
            })

    # Deduplicate by tuple of (name,email,phone)
    unique = []
    seen = set()
    for c in contacts:
        key = (c.get("name", ""), c.get("email", ""), c.get("phone", ""))
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _extract_first_match(text: str, patterns: List[str]) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, flags=re.I | re.M)
        if m:
            grp = m.group(1).strip()
            # Avoid capturing full sentences accidentally
            if len(grp) <= 120:
                return grp
    return None

