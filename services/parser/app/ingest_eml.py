from __future__ import annotations
import hashlib
import email
from email.message import Message
from email import policy
from datetime import datetime, timezone
from typing import Dict, List

from .normalize import normalize_email, normalize_phone, normalize_name
from .extract import extract_contacts_freeform


def parse_eml_bytes(data: bytes) -> Dict:
    msg: Message = email.message_from_bytes(data, policy=policy.default)

    mid = msg.get("Message-ID") or msg.get("Message-Id")
    if not mid:
        # Stable hash of headers + date as fallback
        h = hashlib.sha256()
        h.update((msg.get("From", "") + msg.get("Date", "") + msg.get("Subject", "")).encode("utf-8", errors="ignore"))
        mid = f"<hash-{h.hexdigest()[:32]}@local>"

    date_hdr = msg.get("Date")
    try:
        # Let email library parse date; fallback to now
        dt = email.utils.parsedate_to_datetime(date_hdr) if date_hdr else None
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        dt = None
    received_at_iso = (dt or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()

    from_name, from_email_addr = email.utils.parseaddr(msg.get("From", ""))
    from_email_norm = normalize_email(from_email_addr)

    # Extract plain text body
    body_text = _get_plain_text(msg)

    # Heuristic OOO flag (but we parse everything either way)
    auto = (msg.get("Auto-Submitted", "").lower() not in ("", "no"))
    subject = (msg.get("Subject") or "").lower()
    is_ooo = auto or ("out of office" in subject) or ("auto-reply" in subject)

    # Attribution (optional for now)
    campaign_id = msg.get("X-Campaign-Id", "")
    recipient_id = msg.get("X-Recipient-Id", "")

    # Freeform extraction
    raw_contacts = extract_contacts_freeform(body_text)

    rows: List[Dict] = []
    for c in raw_contacts:
        rows.append({
            "message_id": mid,
            "received_at_iso": received_at_iso,
            "from_email": from_email_norm,
            "from_name": normalize_name(from_name),
            "contact_name": normalize_name(c.get("name")),
            "contact_title": c.get("title", "") or "",
            "contact_company": c.get("company", "") or "",
            "contact_email": normalize_email(c.get("email")),
            "contact_phone_e164": normalize_phone(c.get("phone")),
            "is_ooo": str(bool(is_ooo)).lower(),
            "campaign_id": campaign_id,
            "recipient_id": recipient_id,
            "raw_excerpt": (body_text[:1500] if body_text else ""),
        })
    # If no contacts found, still emit a placeholder row referencing the message
    if not rows:
        rows.append({
            "message_id": mid,
            "received_at_iso": received_at_iso,
            "from_email": from_email_norm,
            "from_name": normalize_name(from_name),
            "contact_name": "",
            "contact_title": "",
            "contact_company": "",
            "contact_email": "",
            "contact_phone_e164": "",
            "is_ooo": str(bool(is_ooo)).lower(),
            "campaign_id": campaign_id,
            "recipient_id": recipient_id,
            "raw_excerpt": (body_text[:1500] if body_text else ""),
        })
    return {"rows": rows}


def _get_plain_text(msg: Message) -> str:
    if msg.is_multipart():
        # Prefer text/plain parts
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    return part.get_content().strip()
                except Exception:
                    try:
                        return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore").strip()
                    except Exception:
                        continue
        # Fallback to first part
        try:
            return msg.get_body(preferencelist=('plain', 'html')).get_content().strip()
        except Exception:
            pass
    try:
        return msg.get_content().strip()
    except Exception:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore").strip()
        except Exception:
            return ""

