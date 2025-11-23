Parser service (reply ingestor)

Summary
- Python 3.11 container that parses email replies (.eml or IMAP later), extracts contact details, normalizes them, and appends rows to /data/out/contacts.csv.
- In test mode, it scans /data/samples for .eml files and exits. IMAP is off by default.

Run (one-line)
docker build -t mail-parser:dev services/parser && docker run --rm -v $(pwd)/data:/data mail-parser:dev python -m app.main --scan-dir /data/samples --once && echo OK

Run tests (one-line)
docker build -t mail-parser:dev services/parser && docker run --rm -v $(pwd)/data:/data mail-parser:dev pytest -q

Config
- OUTPUT_CSV: path to output CSV (default /data/out/contacts.csv)
- LLM_PROVIDER: none|openai|gemini|anthropic|vllm (default none)
- IMAP_*: reserved for future IMAP mode

Notes
- No external API calls by default. LLM is disabled unless LLM_PROVIDER and keys are set.
