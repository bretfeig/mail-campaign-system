# Quick Start Guide - Mail System

## Phase 1: ✅ LOCAL TEST STACK (COMPLETED)

### Services Running
- **Listmonk UI**: http://127.0.0.1:9100 (admin/listmonk)
- **Mailpit UI**: http://127.0.0.1:8025 (SMTP test sink)
- **Grafana**: http://127.0.0.1:3000 (admin/admin)
- **Prometheus**: http://127.0.0.1:9090
- **Metrics API**: http://127.0.0.1:8000/metrics

### What's Working
✅ All containers up and healthy
✅ Listmonk connected to Postgres
✅ Mailpit receiving test emails on port 1025
✅ Metrics/Prometheus/Grafana stack operational

### Next: Configure Listmonk to Send to Mailpit

1. **Access Listmonk**: http://127.0.0.1:9100
   - Login: `admin` / `listmonk`

2. **Configure SMTP** (Settings → SMTP):
   - Click "Add Server"
   - Host: `mailpit`
   - Port: `1025`
   - Auth Protocol: `none`
   - TLS: `Disabled`
   - Max connections: `10`
   - Save

3. **Create Test List**:
   - Lists → New List
   - Name: "Test Campaign"
   - Type: "Public"

4. **Import Subscribers**:
   - Subscribers → Import
   - Paste CSV:
     ```
     email,name
     test1@example.com,John Doe
     test2@example.com,Jane Smith
     ```
   - Select list: "Test Campaign"
   - Import

5. **Create Campaign**:
   - Campaigns → New Campaign
   - Subject: "Test Email"
   - Body:
     ```
     Hi {{ .Subscriber.Name }},

     This is a test email from Listmonk.

     Best,
     Team
     ```
   - Lists: Select "Test Campaign"
   - **Start Campaign**

6. **Verify in Mailpit**:
   - Open http://127.0.0.1:8025
   - You should see 2 emails delivered instantly

---

## Phase 2: DEPLOY MAILCOW (NEXT STEP)

### Prerequisites
- VPS with Ubuntu 22.04+
- Static IP address
- DNS control for `mail.sourceww.com`

### Installation Steps

```bash
cd /opt/mail
git clone https://github.com/mailcow/mailcow-dockerized
cd mailcow-dockerized

# Generate config
./generate_config.sh

# Edit config for localhost testing (initial setup)
nano mailcow.conf
```

**Mailcow.conf changes for localhost testing**:
```bash
MAILCOW_HOSTNAME=mail.sourceww.com
HTTP_PORT=127.0.0.1:8080
HTTPS_PORT=127.0.0.1:8443
SMTP_PORT=127.0.0.1:25
SMTPS_PORT=127.0.0.1:465
SUBMISSION_PORT=127.0.0.1:587
IMAP_PORT=127.0.0.1:143
IMAPS_PORT=127.0.0.1:993
```

```bash
# Pull and start
docker compose pull
docker compose up -d

# Access UI at https://127.0.0.1:8443
# Default login: admin / moohoo
```

### Post-Install Configuration

1. **Create Mailbox** (Mailcow UI → Mailboxes):
   - Email: `replies@mail.sourceww.com`
   - Password: (strong password)
   - Quota: 1GB

2. **Test IMAP**:
   ```bash
   openssl s_client -connect 127.0.0.1:993 -crlf
   # a1 LOGIN replies@mail.sourceww.com PASSWORD
   # a2 LIST "" "*"
   # a3 LOGOUT
   ```

3. **Test SMTP Submission**:
   ```bash
   openssl s_client -connect 127.0.0.1:587 -starttls smtp
   # EHLO test
   # AUTH LOGIN
   # (base64 encode username and password)
   ```

---

## Phase 3: CONNECT LISTMONK → MAILCOW

### Update Listmonk SMTP Settings

**Option A: Use Docker Host IP**
```bash
# Find Docker host IP
ip addr show docker0 | grep inet
# Usually: 172.17.0.1
```

In Listmonk UI → Settings → SMTP:
- Host: `172.17.0.1` (or host.docker.internal on Mac/Windows)
- Port: `587`
- Auth: `PLAIN` or `LOGIN`
- Username: `replies@mail.sourceww.com`
- Password: (mailbox password)
- TLS: `STARTTLS`

**Option B: Add to Docker Network** (cleaner)

Edit `/opt/mail/compose/docker-compose.yml`:
```yaml
  listmonk:
    ...
    extra_hosts:
      - "mail.sourceww.com:172.17.0.1"
```

Then use:
- Host: `mail.sourceww.com`
- Port: `587`

### Test Send

1. Send 1 test email via Listmonk
2. Check Mailcow logs:
   ```bash
   cd /opt/mail/mailcow-dockerized
   docker compose logs -f postfix-mailcow
   ```
3. Verify email delivered to your personal inbox

---

## Phase 4: END-TO-END TEST

1. **Send campaign** from Listmonk with:
   - Reply-To: `replies@mail.sourceww.com`

2. **Reply** from your personal email

3. **Check Mailcow** webmail:
   - https://127.0.0.1:8443/SOGo
   - Login as: `replies@mail.sourceww.com`

4. **Fetch via IMAP** (optional test):
   ```python
   import imaplib
   m = imaplib.IMAP4_SSL('127.0.0.1', 993)
   m.login('replies@mail.sourceww.com', 'PASSWORD')
   m.select('INBOX')
   typ, data = m.search(None, 'ALL')
   print(f"Messages: {data[0].split()}")
   m.logout()
   ```

---

## Phase 5: PRODUCTION DEPLOYMENT

### DNS Setup (Squarespace)

Add these records for `sourceww.com`:

```
Type  Name                          Value                           TTL
A     mail.sourceww.com             <VPS_IP>                        3600
MX    mail.sourceww.com             10 mail.sourceww.com            3600
TXT   mail.sourceww.com             "v=spf1 a -all"                 3600
TXT   _dmarc.mail.sourceww.com      "v=DMARC1; p=none; rua=mailto:dmarc@mail.sourceww.com"  3600
```

**DKIM** (after Mailcow setup):
1. Mailcow UI → Configuration → Configuration & Details → DKIM
2. Copy public key
3. Add TXT record:
   ```
   Type  Name                                Value
   TXT   dkim._domainkey.mail.sourceww.com   <public_key_from_mailcow>
   ```

### Expose Mailcow to Internet

Edit `/opt/mail/mailcow-dockerized/mailcow.conf`:
```bash
# Remove 127.0.0.1 bindings
HTTP_PORT=80
HTTPS_PORT=443
SMTP_PORT=25
SUBMISSION_PORT=587
IMAPS_PORT=993
```

Restart:
```bash
cd /opt/mail/mailcow-dockerized
docker compose down
docker compose up -d
```

### Verify TLS & DNS

```bash
# Test TLS
echo | openssl s_client -connect mail.sourceww.com:443 2>/dev/null | openssl x509 -noout -subject

# Test DKIM/SPF
# Send test email from replies@mail.sourceww.com to check-auth@verifier.port25.com
# Check response for PASS results
```

---

## Phase 6: (OPTIONAL) SES RELAY

### When to Use
- If Mailcow IP reputation is poor
- For high-volume sends (1k-2k/day)

### Setup

1. **AWS SES**:
   - Request production access
   - Verify `mail.sourceww.com`
   - Create SMTP credentials

2. **Mailcow Postfix Config**:
   ```bash
   docker exec -it mailcowdockerized-postfix-mailcow-1 bash
   nano /etc/postfix/main.cf
   ```

   Add:
   ```
   relayhost = [email-smtp.us-east-1.amazonaws.com]:587
   smtp_sasl_auth_enable = yes
   smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
   smtp_sasl_security_options = noanonymous
   smtp_tls_security_level = encrypt
   ```

3. **SMTP Credentials**:
   ```bash
   echo "[email-smtp.us-east-1.amazonaws.com]:587 AKIAXXXXXXX:SES_SMTP_PASSWORD" > /etc/postfix/sasl_passwd
   postmap /etc/postfix/sasl_passwd
   chmod 600 /etc/postfix/sasl_passwd*
   postfix reload
   ```

---

## Troubleshooting

### Listmonk won't start
```bash
docker compose -f compose/docker-compose.yml logs listmonk
# Check for DB connection errors
docker compose -f compose/docker-compose.yml exec postgres pg_isready -U listmonk
```

### Mailcow ports conflict
```bash
# Check what's using ports
netstat -tlnp | grep -E ':(25|80|443|587|993)'
# Stop conflicting services or change ports in mailcow.conf
```

### Emails not delivering
```bash
# Check Mailcow logs
cd /opt/mail/mailcow-dockerized
docker compose logs -f postfix-mailcow | grep -i error

# Test DNS
dig +short mail.sourceww.com
dig +short MX mail.sourceww.com
dig +short TXT mail.sourceww.com
```

### IMAP connection refused
```bash
# Verify Mailcow Dovecot is running
docker compose ps | grep dovecot
docker compose logs dovecot-mailcow
```

---

## Service Management

### Start Everything
```bash
cd /opt/mail
docker compose -f compose/docker-compose.yml up -d

cd /opt/mail/mailcow-dockerized
docker compose up -d
```

### Stop Everything
```bash
docker compose -f compose/docker-compose.yml down
cd /opt/mail/mailcow-dockerized && docker compose down
```

### View Logs
```bash
# Listmonk
docker compose -f compose/docker-compose.yml logs -f listmonk

# Mailcow Postfix
cd /opt/mail/mailcow-dockerized
docker compose logs -f postfix-mailcow
```

---

## Campaign Best Practices

1. **Always test with Mailpit first** (MODE=test)
2. **Use Reply-To headers**: `replies@mail.sourceww.com`
3. **Monitor Mailcow queue**: Check `/var/spool/postfix/deferred` for bounces
4. **Rate limiting**: Start with 100/hour, increase gradually
5. **Check deliverability**: https://www.mail-tester.com/

---

## Decommissioning (After Campaign)

```bash
# Stop and remove all containers
cd /opt/mail
docker compose -f compose/docker-compose.yml down -v

cd /opt/mail/mailcow-dockerized
docker compose down -v

# Delete VPS (if cloud hosted)

# Remove DNS records for mail.sourceww.com
```

Your main domain `sourceww.com` catch-all remains untouched!
