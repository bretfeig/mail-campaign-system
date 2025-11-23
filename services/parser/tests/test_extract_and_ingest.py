import os
from app.ingest_eml import parse_eml_bytes
from app.csv_writer import ensure_header
from app.config import CSV_HEADER


def load_sample(name: str) -> bytes:
    path = os.path.join("/data", "samples", name)
    with open(path, "rb") as f:
        return f.read()


def test_parse_sample_reply_with_contact(tmp_path):
    data = load_sample("reply_signature_1.eml")
    out = parse_eml_bytes(data)
    rows = out["rows"]
    assert isinstance(rows, list)
    # Expect at least one contact
    assert any(r.get("contact_email") for r in rows)
    # Validate all required columns exist
    for r in rows:
        for k in CSV_HEADER:
            assert k in r

