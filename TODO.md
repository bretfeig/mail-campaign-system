# End-to-End TODO + Test Checklist (localhost-only)

Owner: sourceww.com
Purpose: Run one-liner tests for each component. All ports bind to 127.0.0.1 to avoid external exposure.
**Last Updated**: 2025-11-23

Legend
- [ ] pending, [x] done locally

## 0) Bring up stack
- [x] Start (build + up):
  docker compose --env-file compose/.env.example -f compose/docker-compose.yml up -d --build
- [x] List services:
  docker compose -f compose/docker-compose.yml ps
- [x] Tail logs (optional):
  docker compose -f compose/docker-compose.yml logs --no-log-prefix --tail=200

## 1) Postgres (Listmonk DB)
- [x] Health check:
  docker compose -f compose/docker-compose.yml exec -T postgres pg_isready -U listmonk -d listmonk

## 2) Listmonk (sender) - NOTE: UI on port 9100 (not 9000)
- [x] UI reachable (HTTP 200/302 expected):
  curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9100 | grep -E "^(200|302)$"
- [ ] Configure SMTP in UI to host=mailpit port=1025 (no TLS/auth) — manual step

## 3) Mailpit (SMTP sink)
- [x] UI reachable:
  curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8025 | grep -E "^(200|302)$"
- [ ] Send a test email to Mailpit via Python SMTP (should then appear in Mailpit UI):
  python -c "import smtplib; s=smtplib.SMTP('127.0.0.1',1025,timeout=5); s.sendmail('sender@example.com',['rcpt@example.com'],'From: sender@example.com\nTo: rcpt@example.com\nSubject: test via Python\n\nHello from unit test'); s.quit(); print('OK')"

## 4) Parser (test-mode .eml scan)
- [x] Build parser image:
  docker build -t mail-parser:dev services/parser
- [ ] Unit tests (NOTE: tests/ not included in Docker image - needs Dockerfile update):
  docker run --rm -v $(pwd)/data:/data mail-parser:dev pytest -q
- [x] One-shot parse of samples to CSV:
  docker run --rm -v $(pwd)/data:/data mail-parser:dev python -m app.main --scan-dir /data/samples --once
- [x] Inspect CSV (first 20 lines):
  sed -n '1,20p' data/out/contacts.csv

## 5) Metrics service → Prometheus
- [x] Metrics endpoint exposes counters:
  curl -fsS http://127.0.0.1:8000/metrics | grep -E "csv_contacts_total_rows|csv_contacts_unique_contacts|csv_contacts_ooo_count"
- [x] Prometheus up (targets loaded):
  curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9090 | grep -E "^(200|302)$"
- [x] Prometheus query returns success:
  curl -fsS "http://127.0.0.1:9090/api/v1/query?query=csv_contacts_total_rows" | grep '"status":"success"'

## 6) Grafana dashboard
- [x] UI up (login page):
  curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/login | grep -E "^(200|302)$"
- [ ] Login (admin/admin) in browser and open dashboard "Contacts Overview" — manual step

## 7) Listmonk send path (local test)
- [ ] Create a small test list + campaign via UI — manual step
- [ ] Send to 1–2 test recipients; verify messages land in Mailpit UI — manual step

## 8) Attribution wiring (pending)
- [ ] Add Listmonk template with custom headers:
  - X-Campaign-Id: {{ .Campaign.UUID }}
  - X-Recipient-Id: {{ .Subscriber.UUID }}
- [ ] Set Reply-To to: campaign+{{ .Subscriber.UUID }}@sourceww.com
- [ ] Confirm headers appear in Mailpit raw view — manual step

## 9) Parser IMAP mode (pending)
- [ ] Implement IMAP ingestion in parser and add tests (coming in code)
- [ ] Configure env (IMAP_HOST/IMAP_USER/IMAP_PASS) to point at Mailcow (later)
- [ ] Dry-run against a test mailbox (tag processed), verify CSV append

## 10) Mailcow (configured but not running)
- [x] Add Mailcow stack (bind HTTP/HTTPS to 127.0.0.1:8090/8443)
- [x] Configuration generated at mailcow-dockerized/mailcow.conf
- [x] Hostname set to mail.sourceww.com
- [ ] Start Mailcow stack:
  cd /opt/mail/mailcow-dockerized && docker compose up -d
- [ ] Confirm webmail reachable on https://127.0.0.1:8443 (self-signed during local test)
- [ ] Create mailbox for ingestion; test IMAP login (openssl s_client) — manual step
- [ ] Send a reply into Mailcow inbox (via Mailpit export/import or direct SMTP from Listmonk in prod later)

## 11) SES relay (pending for prod)
- [ ] Request SES prod access; verify domain; create SMTP creds — console step
- [ ] Configure Mailcow Postfix relayhost to SES; restart Postfix
- [ ] Switch Listmonk SMTP to Mailcow submission; send 1–2 real messages (later)

## 12) Teardown
- [ ] Stop and remove stack (destructive: removes volumes):
  docker compose -f compose/docker-compose.yml down -v

## Acceptance Snapshot
- [x] Prometheus metrics show >0 csv_contacts_total_rows after parser run (showing 4 rows)
- [x] CSV contains rows with normalized emails/phones for sample .eml
- [ ] Grafana dashboard panels display non-zero values (UI up, dashboard pending)
- [x] Listmonk UI accessible (port 9100)
- [ ] Listmonk SMTP configured to Mailpit

## Current Status (2025-11-23)
- **Listmonk Stack**: ✅ RUNNING (7 containers)
- **Mailcow Stack**: ⚠️ CONFIGURED but NOT RUNNING (13 containers created)
- **Parser**: ✅ WORKING (processes .eml files, outputs CSV)
- **DNS**: ✅ CONFIGURED (mail.sourceww.com → 94.72.114.31)
- **Next Steps**: Start Mailcow, configure Listmonk SMTP, test end-to-end flow

See BUILD_STATUS.md for detailed evaluation and next steps.

