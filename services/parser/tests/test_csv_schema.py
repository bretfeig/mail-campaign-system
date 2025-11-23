from app.config import CSV_HEADER


def test_csv_header_schema_is_fixed():
    assert CSV_HEADER == [
        "message_id",
        "received_at_iso",
        "from_email",
        "from_name",
        "contact_name",
        "contact_title",
        "contact_company",
        "contact_email",
        "contact_phone_e164",
        "is_ooo",
        "campaign_id",
        "recipient_id",
        "raw_excerpt",
    ]

