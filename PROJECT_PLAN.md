# Dockerized High-Volume Email System — Project Plan

Owner: sourceww.com
Status: In progress — local stack scaffolded (Listmonk, Postgres, Mailpit, Parser, Metrics, Prometheus, Grafana) with localhost-only bindings.
Scope: Fully dockerized email send/receive with automated reply parsing to CSV, test mode without SES cost, and production mode with SES failover.

## 1. Goals & Non‑Goals
- Goals
  - Send 1–2k emails/day via a dockerized sender (Listmonk) with SMTP.
  - Receive replies via Mailcow (IMAP/webmail), parse ALL replies (English) for contact details.
  - Extract multiple contacts per message; normalize names, emails, and phone numbers (E.164), and output to a local CSV.
  - Test mode: no SES usage/cost (capture emails locally with Mailpit). Production: switch to SES.
  - Optional: push to Google Sheets later (N8N or direct API).
  - Minimal dashboard: counts of replies/OOO and unique contacts.
- Non‑Goals
  - Inbound via SES (not required; inbound via Mailcow to avoid costs).
  - Suppression lists and SNS bounces (each address is sent once).

## 2. High‑Level Architecture
- Mailcow (dockerized suite) for inbound mail + IMAP + webmail + authentication (MTA: Postfix; IMAP: Dovecot; SOGo for webmail).
- Listmonk for campaign sending (uses SMTP). Postgres for Listmonk state.
- Outbound SMTP target (switchable):
  - Test mode: Mailpit (captures emails; no external cost).
  - Prod mode: Mailcow submission → Postfix relay to Amazon SES (DKIM/SPF/DMARC configured).
- Reply Ingestor (Python service):
  - IMAP poll/IDLE against Mailcow, idempotent processing, tags processed messages.
  - LLM‑assisted contact extraction (provider‑agnostic adapter: local vLLM or cloud API) with normalization and validation.
  - Writes to `data/out/contacts.csv` (append‑only) with a fixed schema and unit tests.
  - Optional webhook to N8N (for Google Sheets sync) — off by default.
- Optional metrics endpoint (Prometheus) + basic Grafana dashboard.

## 3. Modes & Failover Strategy
- Mode is controlled via `.env` variables consumed by Docker Compose.
- Test mode (default for development)
  - Listmonk SMTP host: `mailpit:1025`. Mailcow still handles inbound.
  - No SES usage at all; validate sender and reply pipeline end‑to‑end locally.
- Production mode
  - Listmonk SMTP host: `mail.sourceww.com:587` (Mailcow submission).
  - Mailcow Postfix `relayhost` set to SES (`email-smtp.<region>.amazonses.com:587`).
  - DNS/rDNS/SPF/DKIM/DMARC configured and verified.
- Switching modes
  - Edit `.env` → `MODE=test|prod` and update SMTP host variables accordingly.
  - A single `docker compose` redeploy flips the path. No code changes required.

## 4. Data Model & CSV Schema
- CSV file: `data/out/contacts.csv` (one row per extracted contact, messages with multiple contacts produce multiple rows sharing the same `message_id`).
- Columns (fixed, validated by tests):
  - `message_id` (string) — RFC822 Message‑ID (if missing, a stable hash).
  - `received_at_iso` (string) — ISO‑8601 UTC timestamp.
  - `from_email` (string) — normalized, lowercase.
  - `from_name` (string) — best‑effort.
  - `contact_name` (string) — primary extracted contact name.
  - `contact_title` (string) — job title if present.
  - `contact_company` (string) — company if present.
  - `contact_email` (string) — validated email if present.
  - `contact_phone_e164` (string) — E.164 format if present.
  - `is_ooo` (boolean) — true if likely OOO/auto‑reply; else false.
  - `campaign_id` (string) — set from outbound header or plus‑address tag (see §6).
  - `recipient_id` (string) — per‑recipient id from outbound header or plus‑address tag.
  - `raw_excerpt` (string) — sanitized body excerpt (first ~1500 chars) for audit.

## 5. Components & Versions (pinned)
- Mailcow: upstream `mailcow-dockerized` (current stable).
- Listmonk: v3.x (with Postgres 15/16).
- Mailpit: latest stable (lightweight Mailhog successor).
- Reply Ingestor: Python 3.11 slim image; dependencies pinned via `requirements.txt`.
  - IMAP: `imapclient` + `backoff`.
  - Parsing: `phonenumbers`, `email-validator`, `python-dateutil`.
  - LLM adapters: optional `openai`/`google-generativeai`/`anthropic` or local `vllm` client.
  - Tests: `pytest`, `pytest-cov`.
- Optional: Prometheus + Grafana (prebuilt dashboard JSON); off by default.

## 6. Attribution Strategy (recommended)
- Use both:
  - Custom headers from Listmonk: `X-Campaign-Id` and `X-Recipient-Id` (UUIDs or sequential ids).
  - Plus‑addressing for Reply‑To: `campaign+<recipient_id>@sourceww.com` (Mailcow supports catch‑all to mailbox; the parser extracts `recipient_id` from the address if present).
- The reply ingestor prioritizes headers; falls back to plus‑address pattern.

## 7. Repository & Directory Layout
```
/opt/mail
├─ compose/
│  ├─ docker-compose.yml           # Orchestration for Listmonk, Postgres, Mailpit, Parser, (optional) Grafana/Prometheus
│  ├─ .env.example                 # Example env for test/prod toggle and secrets placeholders
│  ├─ grafana/                     # Optional dashboard provisioning (off by default)
├─ mailcow-dockerized/             # Mailcow upstream clone lives here (managed separately)
├─ services/
│  ├─ parser/
│  │  ├─ app/                      # Python package
│  │  ├─ tests/                    # Pytest unit & integration tests with canned .eml
│  │  ├─ requirements.txt          # Pinned deps
│  │  ├─ Dockerfile                # Python 3.11 slim
│  │  └─ README.md                 # Local dev/test instructions
│  └─ listmonk/
│     ├─ config/                   # Listmonk config (SMTP etc.)
│     └─ init/                     # Optional init SQL for headers, templates
├─ data/
│  ├─ out/contacts.csv             # Output CSV (mounted volume)
│  └─ samples/                     # Sample outbound lists and canned replies
└─ PROJECT_PLAN.md                 # This plan
```

## 8. Work Plan (Phases, Tasks, Acceptance)

Phase 0 — Prereqs (owner: ops)
- Tasks
  - Provision Ubuntu 22.04+ VPS with static IPv4 and rDNS control.
  - Domain DNS access at Squarespace.
- Acceptance
  - Shell access with `docker` runnable and ports 80/443 open.

Phase 1 — Base Platform (Mailcow)
- Tasks
  - Deploy Mailcow per official docs; set `MAILCOW_HOSTNAME=mail.sourceww.com`.
  - Configure A/MX, SPF (`include:amazonses.com`), DMARC, DKIM; set reverse DNS.
  - Enable ACME in Mailcow for TLS.
- Acceptance
  - Webmail works at `https://mail.sourceww.com/SOGo`.
  - IMAP login succeeds; test mail receives.

Phase 2 — Sender Stack (Listmonk)
- Tasks
  - Add Listmonk + Postgres to `compose/docker-compose.yml` with pinned images.
  - Configure SMTP for test mode (`SMTP_HOST=mailpit`, `SMTP_PORT=1025`).
  - Seed a test list and template; inject custom headers (`X-Campaign-Id`, `X-Recipient-Id`) and set Reply‑To to `campaign+{{recipient_id}}@sourceww.com`.
- Acceptance
  - Test campaign sends to Mailpit; visible in Mailpit UI; zero external sends.

Phase 3 — Test SMTP Sink (Mailpit)
- Tasks
  - Add Mailpit container; expose web UI (e.g., 8025) for manual verification.
  - Sanity: send a single email via Listmonk → confirm in Mailpit.
- Acceptance
  - 100 test emails deliver to Mailpit in <2 minutes, no errors.

Phase 4 — Reply Ingestor (Parser)
- Tasks
  - Scaffold Python service: IMAP poll/IDLE, dedupe by `message_id`/UID, tag processed.
  - Implement LLM adapter interface and a rule‑based baseline fallback.
  - Normalize outputs; write to `data/out/contacts.csv` with fixed columns.
  - Add unit tests with canned `.eml` covering OOO and signature extraction; target >90% precision on samples.
- Acceptance
  - `pytest` passes locally; parser processes sample `.eml` fixtures and appends expected rows.

Phase 5 — Optional Dashboards
- Tasks
  - Expose parser metrics (HTTP) with counts; optional Prometheus + Grafana with a simple panel: total replies, OOO ratio, unique contacts.
- Acceptance
  - Metrics visualize in Grafana (enabled locally) or logs show counts.

Phase 6 — Production Cutover (SES)
- Tasks
  - Request SES production access; verify domain; create SMTP creds.
  - Switch Listmonk SMTP to Mailcow submission (`mail.sourceww.com:587`).
  - Set Mailcow Postfix `relayhost` to SES; secure password maps; restart Postfix.
- Acceptance
  - 10‑message smoke test lands in real inboxes; SES dashboard shows sends without throttling.

Phase 7 — Scale & Operate
- Tasks
  - Run controlled batches; monitor logs; adjust concurrency.
  - Periodic CSV rotation (daily/hourly) and archival.
  - Optional: N8N flow to push new rows to Google Sheets.
- Acceptance
  - Sustained 1–2k/day with stable resource usage; CSV rows match reply volume.

## 9. Testing Strategy
- Unit tests (parser): `.eml` fixtures for OOO and standard replies; assert extracted contacts, phone normalization, and schema.
- Integration: end‑to‑end in test mode — Listmonk → Mailpit (outbound) → import/copy messages into Mailcow mailbox → parser → CSV rows.
- Schema validation: test that `data/out/contacts.csv` header matches expected columns; CI fails on drift.
- Cost guardrails: no external API calls in test mode by default; LLM adapter runs in mock mode unless `LLM_PROVIDER` and `API_KEY` are set.

## 10. Security & Secrets
- `.env` (not committed) holds SMTP creds, IMAP creds for parser, and any LLM API keys.
- Least privilege: parser IMAP user is read‑only if possible; if not, restrict scope and tagging folder.
- No real secrets in configs; use environment variables only.

## 11. Operations & Runbooks
- Start (test mode): ensure `.env` sets `MODE=test`, then `docker compose -f compose/docker-compose.yml up -d`.
- Verify
  - Mailpit UI reachable; send a Listmonk test campaign; emails appear in Mailpit.
  - Move/copy sample replies into the Mailcow mailbox; check that CSV updates.
- Switch to production
  - Update `.env` to `MODE=prod` and set SES SMTP creds in Mailcow; redeploy compose; run 10‑message smoke test.
- Diagnostics (examples)
  - Docker: `docker compose ps`, `docker compose logs -f <service>`
  - Mailcow Postfix relay: `docker compose logs -f postfix-mailcow`
  - Parser: `docker compose logs -f parser`

## 12. Acceptance Criteria (End‑to‑End)
- Test mode: 100 messages sent; 20 canned replies processed; CSV contains correct normalized contacts (multiple per message supported); zero SES usage.
- Production: 10 real messages delivered; 5 real replies parsed to CSV correctly; DKIM/SPF/DMARC pass.
- Documentation: README for parser service and compose usage; `.env.example` provided.

## 13. Next Actions (Updated 2025-11-23)
1) ✅ DONE: Initialize repository structure and base compose (Listmonk, Postgres, Mailpit, Parser skeleton, Metrics, Prometheus, Grafana, data/).
2) ⚠️ PARTIAL: Deploy Mailcow per its own repo under `mailcow-dockerized/` (localhost bindings) - configured but not running.
3) ✅ DONE: Implement parser skeleton + tests with fixtures; test-mode `.eml` scan.
4) TODO: Wire Listmonk headers and plus‑addressing; provide example template.
5) TODO: Add production SES relay in Mailcow; flip to prod mode and smoke test.
6) TODO: Parser IMAP mode against Mailcow to automate reply ingestion.

**Current Status**: ~60% complete. Listmonk stack operational, parser working, DNS configured.
Mailcow needs to be started and tested. See BUILD_STATUS.md for detailed evaluation.

---

Appendix A — Environment Variables (draft)
- Global
  - `MODE` = `test` | `prod`
- Listmonk
  - `LISTMONK_SMTP_HOST`, `LISTMONK_SMTP_PORT` (test: `mailpit:1025`; prod: `mail.sourceww.com:587`)
  - `LISTMONK_SMTP_USER`, `LISTMONK_SMTP_PASS`, `LISTMONK_SMTP_TLS` (prod)
- Parser
  - `IMAP_HOST`, `IMAP_PORT`, `IMAP_USER`, `IMAP_PASS`, `IMAP_SSL=true`
  - `LLM_PROVIDER` (e.g., `none|openai|gemini|anthropic|vllm`)
  - `LLM_MODEL` (string), `LLM_API_KEY` (if using cloud), `LLM_ENDPOINT` (if local vLLM)
  - `OUTPUT_CSV=/data/out/contacts.csv`

Appendix B — LLM Extraction (outline)
- Prompt instructs model to output strict JSON array of contacts with fields: `name`, `title`, `company`, `email`, `phone`.
- Post‑processing: validate emails, normalize phones (E.164), map into rows; fill `is_ooo` heuristically.
- Fallback path: rule‑based regex extractors to keep pipeline working without LLM.

Appendix C — Risks & Mitigations
- Deliverability: rely on SES for production; fully configured SPF/DKIM/DMARC.
- Cost control: Mailpit for test sends; mock LLM by default; cap prod LLM max tokens.
- Parser accuracy: combine LLM + heuristics; iterate with fixtures.
- Data safety: redact and truncate `raw_excerpt`; avoid storing full raw unless needed.
