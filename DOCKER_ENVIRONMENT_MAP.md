# Docker Environment Map - CRITICAL REFERENCE

**Purpose**: Document all Docker services running on this VPS to avoid accidentally affecting ATS/CRM production systems.

**Date Created**: 2025-11-19
**Last Updated**: 2025-11-19

---

## ⚠️ CRITICAL WARNING ⚠️

This server runs **MULTIPLE** docker-compose stacks:
1. **ATS/CRM Production System** (DO NOT TOUCH)
2. **Mail System** (at `/opt/mail/` - this project)
3. **Backend Services** (LinkedIn scraper, Tika, etc.)

**ALWAYS** use explicit paths when running docker compose commands!

---

## Running Container Inventory

### 🔴 **ATS/CRM Production Containers** (DO NOT STOP)
```
NAME                        IMAGE                   PORTS                      PURPOSE
------------------------------------------------------------------------------------------------------
candidate_api               backend-api             127.0.0.1:3001->3001       ATS/CRM API server
candidate_db                postgres:16-alpine      127.0.0.1:5433->5432       ATS/CRM Database
candidate_redis             redis:7-alpine          127.0.0.1:6379->6379       ATS/CRM Cache
candidate_minio             minio/minio:latest      127.0.0.1:9000-9001        ATS/CRM Object Storage
ats_frontend                node:20-alpine          -                          ATS Frontend
ats_frontend_sandbox        node:20-alpine          -                          ATS Frontend Sandbox
```

### 🟡 **Backend/Support Services** (DO NOT STOP)
```
NAME                        IMAGE                              PORTS                   PURPOSE
------------------------------------------------------------------------------------------------------
linkedin-scraper-backend    backend-linkedin-scraper-backend   0.0.0.0:8001->8001      LinkedIn Data Scraper
tika                        apache/tika:3.2.2.0-full          127.0.0.1:9998->9998    Document Processing
```

### 🟢 **Mail System Containers** (This Project - Safe to Manage)

#### Listmonk Stack (compose/docker-compose.yml)
```
NAME                    IMAGE                       PORTS                               PURPOSE
------------------------------------------------------------------------------------------------------
mail_listmonk           listmonk/listmonk:latest    127.0.0.1:9100->9000               Email Campaign Manager
mail_postgres           postgres:16-alpine          5432 (internal)                     Listmonk Database
mail_mailpit            axllent/mailpit:latest      127.0.0.1:1025, 8025               SMTP Test Sink
mail_metrics            compose-metrics             127.0.0.1:8000                      Prometheus Exporter
mail_prometheus         prom/prometheus:v2.55.0     127.0.0.1:9090                      Metrics Collector
mail_grafana            grafana/grafana:11.2.0      127.0.0.1:3000                      Metrics Dashboard
```

#### Mailcow Stack (mailcow-dockerized/)
```
NAME                                         IMAGE                           PORTS                           PURPOSE
------------------------------------------------------------------------------------------------------------------------------
mailcowdockerized-nginx-mailcow-1            ghcr.io/mailcow/nginx:1.05      127.0.0.1:8090, 9443           Web UI
mailcowdockerized-postfix-mailcow-1          ghcr.io/mailcow/postfix:1.81    0.0.0.0:25, 465, 587           SMTP Server
mailcowdockerized-dovecot-mailcow-1          ghcr.io/mailcow/dovecot:2.35    0.0.0.0:110, 143, 993, 995     IMAP/POP3
mailcowdockerized-mysql-mailcow-1            mariadb:10.11                   127.0.0.1:13306                Mailcow DB
mailcowdockerized-redis-mailcow-1            redis:7.4.6-alpine              127.0.0.1:7654                 Cache
mailcowdockerized-sogo-mailcow-1             ghcr.io/mailcow/sogo:1.136      -                              Webmail
mailcowdockerized-rspamd-mailcow-1           ghcr.io/mailcow/rspamd:2.4      -                              Spam Filter
mailcowdockerized-clamd-mailcow-1            ghcr.io/mailcow/clamd:1.71      -                              Antivirus
mailcowdockerized-unbound-mailcow-1          ghcr.io/mailcow/unbound:1.24    53 (internal)                  DNS Resolver
(+ 11 more Mailcow support containers)
```

---

## Docker Networks

```
NETWORK NAME                        SCOPE       USED BY
------------------------------------------------------------------------------------------------------
ats-sandbox_default                 bridge      ATS Frontend Sandbox
backend_default                     bridge      LinkedIn Scraper, Backend Services
compose_default                     bridge      Mail System (Listmonk stack)
mailcowdockerized_mailcow-network   bridge      Mailcow stack
sandbox_default                     bridge      Sandbox environments
bridge                              bridge      Default Docker network
host                                host        Host networking
none                                null        Null network
```

---

## Docker Compose File Locations

```
🔴 ATS/CRM:           /opt/ats/talent-stream-engine/backend/docker-compose.yml
🟡 Backend/Scraper:   (likely in /opt/ats/ or related directory)
🟢 Mail Listmonk:     /opt/mail/compose/docker-compose.yml
🟢 Mailcow:           /opt/mail/mailcow-dockerized/docker-compose.yml
```

---

## Port Allocation Summary

### Localhost-only Bindings (Safe)
```
127.0.0.1:3000   → mail_grafana
127.0.0.1:3001   → candidate_api (ATS) 🔴
127.0.0.1:5433   → candidate_db (ATS) 🔴
127.0.0.1:6379   → candidate_redis (ATS) 🔴
127.0.0.1:7654   → mailcowdockerized-redis-mailcow-1
127.0.0.1:8000   → mail_metrics
127.0.0.1:8025   → mail_mailpit
127.0.0.1:8090   → mailcowdockerized-nginx-mailcow-1 (HTTP)
127.0.0.1:9000   → candidate_minio (ATS) 🔴
127.0.0.1:9001   → candidate_minio (ATS) 🔴
127.0.0.1:9090   → mail_prometheus
127.0.0.1:9100   → mail_listmonk
127.0.0.1:9443   → mailcowdockerized-nginx-mailcow-1 (HTTPS)
127.0.0.1:9998   → tika 🟡
127.0.0.1:13306  → mailcowdockerized-mysql-mailcow-1
127.0.0.1:19991  → mailcowdockerized-dovecot-mailcow-1
```

### Internet-facing Bindings (0.0.0.0)
```
0.0.0.0:25       → mailcowdockerized-postfix-mailcow-1 (SMTP)
0.0.0.0:110      → mailcowdockerized-dovecot-mailcow-1 (POP3)
0.0.0.0:143      → mailcowdockerized-dovecot-mailcow-1 (IMAP)
0.0.0.0:465      → mailcowdockerized-postfix-mailcow-1 (SMTPS)
0.0.0.0:587      → mailcowdockerized-postfix-mailcow-1 (Submission)
0.0.0.0:993      → mailcowdockerized-dovecot-mailcow-1 (IMAPS)
0.0.0.0:995      → mailcowdockerized-dovecot-mailcow-1 (POP3S)
0.0.0.0:4190     → mailcowdockerized-dovecot-mailcow-1 (ManageSieve)
0.0.0.0:8001     → linkedin-scraper-backend 🟡
```

---

## Safe Docker Command Patterns

### ✅ SAFE - Use these patterns:
```bash
# Mail system (Listmonk)
cd /opt/mail
docker compose -f compose/docker-compose.yml ps
docker compose -f compose/docker-compose.yml logs listmonk
docker compose -f compose/docker-compose.yml restart mailpit

# Mail system (Mailcow)
cd /opt/mail/mailcow-dockerized
docker compose ps
docker compose logs postfix-mailcow
docker compose restart nginx-mailcow

# View all containers
docker ps
docker ps -a

# View specific container
docker logs mail_listmonk
docker logs candidate_api
```

### ❌ DANGEROUS - Never run these without explicit paths:
```bash
# DON'T: docker compose down        (could affect ANY stack!)
# DON'T: docker compose restart     (ambiguous which stack)
# DON'T: docker stop $(docker ps -q) (stops EVERYTHING including ATS/CRM)
# DON'T: docker system prune -a     (deletes ATS/CRM images/volumes)
```

---

## Emergency Recovery

If ATS/CRM containers are accidentally stopped:

```bash
# Navigate to ATS/CRM directory and restart
cd /opt/ats/talent-stream-engine/backend
docker compose up -d

# Verify services are back up
docker compose ps
docker compose logs -f --tail=50
```

---

## Monitoring Commands

```bash
# Check resource usage
docker stats --no-stream

# Check which containers are using which networks
docker network inspect compose_default
docker network inspect mailcowdockerized_mailcow-network
docker network inspect backend_default

# Check disk usage
docker system df
```

---

## Notes

- **ATS/CRM Production**: Critical business system - DO NOT DISRUPT
- **Mail System**: Temporary campaign infrastructure (can be safely restarted/stopped)
- **Port Conflicts**: Mail system uses non-standard ports (9100, 8090, 9443) to avoid conflicts
- **Data Persistence**: ATS/CRM likely has critical volumes - never run `docker volume prune`

---

**Last Container Count**: 31 total (12 ATS/CRM, 2 Backend, 17 Mail System)

