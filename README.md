# Dockerized Email Campaign System for sourceww.com

A fully dockerized email sending and reply processing system for high-volume campaigns (1-2k emails/day) with automated contact extraction from replies.

## Quick Links

- **[BUILD_STATUS.md](BUILD_STATUS.md)** - Current implementation status and evaluation
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Complete technical specification
- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup guide
- **[TODO.md](TODO.md)** - Testing checklist with one-liner commands
- **[DOCKER_ENVIRONMENT_MAP.md](DOCKER_ENVIRONMENT_MAP.md)** - Critical reference for multi-stack VPS

## System Overview

### Architecture

```
┌─────────────┐      ┌──────────┐      ┌─────────────┐
│  Listmonk   │─────▶│ Mailpit  │      │   Mailcow   │
│  (Sender)   │      │  (Test)  │      │ (Inbound)   │
└─────────────┘      └──────────┘      └─────────────┘
                            │                  │
                            │                  │ IMAP
                            ▼                  ▼
                     ┌─────────────────────────────┐
                     │   Parser (Python)           │
                     │   - Extract contacts        │
                     │   - Normalize phone/email   │
                     │   - LLM-assisted parsing    │
                     └─────────────────────────────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │ contacts.csv  │
                          └───────────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
              ┌────────────┐          ┌──────────────┐
              │ Prometheus │────────▶ │   Grafana    │
              │  (Metrics) │          │ (Dashboard)  │
              └────────────┘          └──────────────┘
```

### Components

- **Listmonk**: Campaign management and email sending
- **Postgres**: Listmonk database
- **Mailpit**: Test SMTP sink (zero cost testing)
- **Mailcow**: Production mail server (Postfix, Dovecot, SOGo webmail)
- **Parser**: Python service for reply processing with contact extraction
- **Metrics**: Prometheus exporter for CSV data
- **Prometheus**: Time-series metrics storage
- **Grafana**: Visualization dashboard

## Current Status (2025-11-23)

✅ **Operational**: Listmonk stack (7 containers)
⚠️ **Configured but not running**: Mailcow stack
✅ **Working**: Parser service processing .eml files
✅ **Configured**: DNS (mail.sourceww.com)

See [BUILD_STATUS.md](BUILD_STATUS.md) for detailed evaluation.

## Quick Start

### Prerequisites

- Ubuntu 22.04+ VPS
- Docker and Docker Compose
- Domain with DNS control (mail.sourceww.com)

### 1. Start Listmonk Stack

```bash
cd /opt/mail
docker compose -f compose/docker-compose.yml up -d
```

**Access**:
- Listmonk: http://127.0.0.1:9100 (admin/listmonk)
- Mailpit: http://127.0.0.1:8025
- Grafana: http://127.0.0.1:3000 (admin/admin)
- Prometheus: http://127.0.0.1:9090

### 2. Configure Listmonk SMTP

1. Open Listmonk UI: http://127.0.0.1:9100
2. Settings → SMTP → Add Server
   - Host: `mailpit`
   - Port: `1025`
   - TLS: Disabled
   - Auth: None

### 3. Test Send Campaign

1. Create a list and import subscribers
2. Create a campaign
3. Send campaign
4. Verify emails in Mailpit: http://127.0.0.1:8025

### 4. Deploy Mailcow (Optional - for inbound)

```bash
cd /opt/mail/mailcow-dockerized
docker compose up -d
```

Access webmail: https://127.0.0.1:8443 (admin/moohoo)

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## Testing Parser

```bash
# Build parser image
docker build -t mail-parser:dev services/parser

# Process sample .eml files
docker run --rm -v $(pwd)/data:/data mail-parser:dev \
  python -m app.main --scan-dir /data/samples --once

# View results
cat data/out/contacts.csv
```

## Configuration

### Test Mode (Default)
- Listmonk → Mailpit (port 1025)
- No external sends
- Zero cost

### Production Mode
- Listmonk → Mailcow submission (port 587)
- Mailcow → Amazon SES relay
- DNS/SPF/DKIM/DMARC configured

See `compose/.env.example` for environment variables.

## Project Structure

```
/opt/mail/
├── compose/              # Docker Compose for Listmonk stack
│   ├── docker-compose.yml
│   ├── .env.example
│   └── grafana/          # Dashboard provisioning
├── services/
│   ├── parser/           # Python reply processing service
│   └── metrics/          # Prometheus exporter
├── data/
│   ├── out/              # CSV output (contacts.csv)
│   └── samples/          # Test .eml files
├── mailcow-dockerized/   # Mailcow upstream (separate git repo)
└── *.md                  # Documentation
```

## Features

### Email Sending
- Campaign management via Listmonk UI
- Template support with variables
- Custom headers (X-Campaign-Id, X-Recipient-Id)
- Plus-addressing for attribution (campaign+id@domain.com)
- Test mode with zero cost

### Reply Processing
- Automatic IMAP polling (planned)
- Contact extraction from signatures
- Multiple contacts per message
- Phone normalization (E.164 format)
- Email validation and normalization
- OOO detection
- CSV output with fixed schema

### Observability
- Prometheus metrics
- Grafana dashboards
- Contact count tracking
- OOO ratio monitoring

## CSV Output Schema

```csv
message_id,received_at_iso,from_email,from_name,contact_name,contact_title,
contact_company,contact_email,contact_phone_e164,is_ooo,campaign_id,
recipient_id,raw_excerpt
```

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed schema documentation.

## Security Notes

**Development** (localhost-only):
- All ports bound to 127.0.0.1
- No external exposure
- Self-signed certificates OK

**Production** (when ready):
- Change default passwords
- Configure Let's Encrypt TLS
- Enable fail2ban
- Verify SPF/DKIM/DMARC
- Review firewall rules

## Maintenance

### View Logs
```bash
# Listmonk
docker compose -f compose/docker-compose.yml logs -f listmonk

# Parser
docker compose -f compose/docker-compose.yml logs parser

# Mailcow Postfix
cd mailcow-dockerized
docker compose logs -f postfix-mailcow
```

### Stop Services
```bash
# Listmonk stack
docker compose -f compose/docker-compose.yml down

# Mailcow stack
cd mailcow-dockerized
docker compose down
```

## Next Steps

1. Start Mailcow stack
2. Configure Listmonk SMTP to Mailpit
3. Test end-to-end campaign flow
4. Implement parser IMAP mode
5. Configure SES relay (production)

See [TODO.md](TODO.md) for testing checklist.

## Troubleshooting

### Listmonk won't start
```bash
docker compose -f compose/docker-compose.yml logs listmonk
docker compose -f compose/docker-compose.yml exec postgres pg_isready -U listmonk
```

### Port conflicts
```bash
netstat -tlnp | grep -E ':(25|80|443|587|993)'
# Mail system uses non-standard ports to avoid conflicts
```

### Parser errors
```bash
docker logs mail_parser
# Check data/out/ permissions
# Verify sample .eml files exist
```

## Documentation

- **BUILD_STATUS.md** - Current state and evaluation (read this first!)
- **PROJECT_PLAN.md** - Complete technical specification
- **QUICKSTART.md** - Phase-by-phase setup guide
- **TODO.md** - Testing checklist with commands
- **DOCKER_ENVIRONMENT_MAP.md** - Multi-stack environment reference

## License

Internal project for sourceww.com

## Support

For issues or questions, see BUILD_STATUS.md for current known issues and next steps.
