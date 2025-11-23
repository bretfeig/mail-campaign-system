import os


OUTPUT_CSV = os.getenv("OUTPUT_CSV", "/data/out/contacts.csv")

MODE = os.getenv("MODE", "test")

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
IMAP_SSL = os.getenv("IMAP_SSL", "true").lower() == "true"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none")  # none|openai|gemini|anthropic|vllm
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")

CSV_HEADER = [
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
