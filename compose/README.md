Local stack (localhost-only)

Summary
- Runs Listmonk, Postgres, Mailpit, parser (test-mode), metrics, Prometheus, and Grafana. All ports bind to 127.0.0.1 only.

Start stack (one-line)
docker compose --env-file compose/.env.example -f compose/docker-compose.yml up -d --build

Open UIs
- Listmonk: http://127.0.0.1:9000
- Mailpit: http://127.0.0.1:8025
- Prometheus: http://127.0.0.1:9090
- Grafana: http://127.0.0.1:3000 (admin/admin)

Run parser tests (one-line)
docker build -t mail-parser:dev services/parser && docker run --rm -v $(pwd)/data:/data mail-parser:dev pytest -q

Re-run parser once on samples (one-line)
docker run --rm -v $(pwd)/data:/data mail-parser:dev python -m app.main --scan-dir /data/samples --once

Stop stack (one-line)
docker compose -f compose/docker-compose.yml down -v

Note
- Listmonk SMTP should be set to host "mailpit" port 1025 (no TLS/auth) via Listmonk UI.
