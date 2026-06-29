# Security Guide

This project is a defensive Website Firewall / mini WAF for Termux.

It works as a reverse proxy:

```text
Visitor / Browser
        ↓
Mraprguild Termux Website Firewall
        ↓
Your real website / backend
```

The firewall checks each HTTP request before forwarding it to the real backend.

---

## 1. Security goal

The goal is to reduce common website attack traffic before it reaches your app.

It helps against:

- Basic SQL injection payloads
- Basic cross-site scripting payloads
- Path traversal attempts
- Sensitive file requests
- Known bad scanner User-Agents
- Excessive requests from one IP
- Oversized request bodies

It does not replace secure coding, authentication, HTTPS, server patching, backups, or Cloudflare/Nginx/hosting security.

---

## 2. Threat model

### Protected assets

- Website admin panel
- User account pages
- Upload/download pages
- API endpoints
- Website files and configs
- Backend server resources

### Common attacks this project tries to reduce

| Attack type | Example target | Defense in this project |
|---|---|---|
| SQL injection | Search, login, ID parameter | Regex payload detection |
| XSS | Comment box, URL parameters | Script/event-handler blocking |
| Path traversal | File download endpoints | `../`, `/etc/passwd`, `php://` rules |
| Sensitive file access | `.env`, `wp-config.php`, DB dumps | `blocked_paths` |
| Bot scanning | WordPress/plugin probing | Bad User-Agent list |
| Request flood | Too many requests from one IP | Rate limiting |
| Large body abuse | Oversized upload/body | Body size limit |

---

## 3. Important limitations

This is a lightweight educational/defensive WAF.

Do not think of it as full enterprise protection.

Limitations:

- Regex rules can miss encoded or advanced payloads.
- False positives can happen.
- It cannot fix vulnerable application code.
- It does not provide HTTPS by itself.
- It does not stop large network DDoS attacks.
- Termux on Android is not ideal for production hosting.
- If traffic does not pass through this firewall, it cannot be protected.
- If your real backend is still public, attackers can bypass the firewall.

For production, use a real VPS/cloud server with Nginx/Caddy/Cloudflare/ModSecurity/OWASP CRS or managed WAF.

---

## 4. Safe deployment architecture

### Good local testing architecture

```text
Phone browser → 127.0.0.1:8080 → backend 127.0.0.1:8000
```

### Good LAN testing architecture

```text
LAN device → PHONE_IP:8080 → backend 127.0.0.1:8000
```

### Production-style architecture

```text
Internet
  ↓
Cloudflare / VPS firewall / Nginx HTTPS
  ↓
Mraprguild WAF reverse proxy
  ↓
Private backend app
```

Make sure the backend is not directly reachable from the internet.

---

## 5. Configuration file

Main file:

```bash
nano config.yml
```

### Upstream

```yml
upstream: "http://127.0.0.1:8000"
```

This is your real website/backend.

### Firewall listen port

```yml
listen_host: "0.0.0.0"
listen_port: 8080
```

Use port `8080` on Termux. Ports below `1024` usually require elevated privileges on Linux-like systems.

### Body size limit

```yml
max_body_bytes: 2097152
```

Default: 2 MB.

For upload sites, increase carefully.

Examples:

```yml
# 50 MB
max_body_bytes: 52428800

# 200 MB
max_body_bytes: 209715200
```

### Rate limit

```yml
rate_limit_requests: 80
rate_limit_seconds: 60
```

Means one IP can make 80 requests per 60 seconds.

Strict example:

```yml
rate_limit_requests: 30
rate_limit_seconds: 60
```

Upload/download sites may need a higher limit.

---

## 6. Security modules

Enable/disable in `config.yml`:

```yml
modules:
  sql_injection: true
  xss: true
  path_traversal: true
  command_injection: true
  bad_bots: true
  rate_limit: true
  block_sensitive_paths: true
```

Keep all enabled unless you find a false positive.

---

## 7. Blocked sensitive paths

Default blocked examples:

```yml
blocked_paths:
  - "/.env"
  - "/wp-config.php"
  - "/config.php"
  - "/backup.zip"
  - "/database.sql"
  - "/phpmyadmin"
  - "/xmlrpc.php"
```

For WordPress, also consider:

```yml
  - "/wp-admin/install.php"
  - "/wp-admin/setup-config.php"
  - "/readme.html"
  - "/license.txt"
```

Do not block `/wp-admin` if you need admin login through this firewall.

---

## 8. IP allow/block lists

Files:

```text
rules/allowed_ips.txt
rules/blocked_ips.txt
```

Block one IP:

```bash
echo "1.2.3.4" >> rules/blocked_ips.txt
```

Block subnet:

```bash
echo "1.2.3.0/24" >> rules/blocked_ips.txt
```

Allow trusted IP:

```bash
echo "1.2.3.4" >> rules/allowed_ips.txt
```

Allowed IPs bypass rule checks, so only add trusted IPs.

---

## 9. Bad bot rules

File:

```bash
nano rules/bad_bots.txt
```

Default blocked scanner keywords:

```text
sqlmap
nikto
acunetix
nessus
masscan
nmap
dirbuster
gobuster
ffuf
wpscan
zgrab
```

`curl` and `wget` are not blocked by default because they are useful for local testing. Add them only if you do not need command-line testing:

```bash
echo "curl" >> rules/bad_bots.txt
echo "wget" >> rules/bad_bots.txt
```

---

## 10. Logs

Blocked requests are saved here:

```bash
logs/blocked.log
```

Watch live:

```bash
tail -f logs/blocked.log
```

Each line is JSON:

```json
{"time":"2026-06-29T10:00:00+05:30","ip":"127.0.0.1","method":"GET","path":"/?id=1 union select","status":403,"reason":"sql_injection rule matched","user_agent":"curl/8"}
```

Recommended monitoring:

- Check repeated IPs.
- Check repeated blocked paths.
- Tune false positives.
- Move serious attackers to `rules/blocked_ips.txt`.
- Save log backups before deleting old logs.

---

## 11. Security testing

Run demo backend in one Termux session:

```bash
bash demo_backend.sh
```

Run firewall in another Termux session:

```bash
bash start.sh
```

Then run:

```bash
bash security_test.sh
```

Manual clean test:

```bash
curl -i http://127.0.0.1:8080/
```

Manual SQLi block test:

```bash
curl -i "http://127.0.0.1:8080/?id=1%20union%20select%20password%20from%20users"
```

Manual XSS block test:

```bash
curl -i "http://127.0.0.1:8080/?q=%3Cscript%3Ealert(1)%3C/script%3E"
```

Manual sensitive file block test:

```bash
curl -i http://127.0.0.1:8080/.env
```

Run tests only against your own local firewall.

---

## 12. WordPress protection notes

For WordPress sites:

Recommended blocked paths:

```yml
blocked_paths:
  - "/.env"
  - "/wp-config.php"
  - "/xmlrpc.php"
  - "/readme.html"
  - "/license.txt"
  - "/backup.zip"
  - "/database.sql"
```

Keep plugins/themes updated.

Use strong admin password.

Disable unused plugins.

Use official plugin/theme sources.

Use HTTPS on production.

Back up database and uploads.

---

## 13. Upload/download website notes

For file upload/download websites:

- Increase `max_body_bytes` only as needed.
- Use login-required uploads.
- Validate file extensions on backend.
- Store uploads outside public webroot when possible.
- Rename uploaded files safely.
- Never execute uploaded PHP/JS/HTML files.
- Scan suspicious files before sharing publicly.
- Use signed or temporary download links for private files.

---

## 14. HTTPS note

This Python firewall does not automatically create HTTPS certificates.

For public production, put it behind:

- Nginx with SSL
- Caddy with automatic HTTPS
- Cloudflare
- Hosting provider reverse proxy

Local testing over HTTP is okay. Public login forms should use HTTPS.

---

## 15. Backup and recovery

Backup important files:

```bash
tar -czf firewall-backup.tar.gz config.yml rules logs
```

Restore:

```bash
tar -xzf firewall-backup.tar.gz
```

Before changing rules:

```bash
cp config.yml config.yml.bak
cp -r rules rules.bak
```

---

## 16. Update checklist

Run regularly:

```bash
pkg update -y
pkg upgrade -y
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt
```

Then restart:

```bash
bash start.sh
```

---

## 17. Production hardening checklist

- [ ] Backend is private and not directly exposed.
- [ ] HTTPS is enabled before public use.
- [ ] Strong admin passwords enabled.
- [ ] App/framework/plugins updated.
- [ ] Firewall logs checked daily.
- [ ] Blocked IP list reviewed.
- [ ] Rate limit tuned.
- [ ] Upload limit tuned.
- [ ] Backups enabled.
- [ ] Security rules tested after updates.
- [ ] False positives reviewed.
- [ ] Admin URLs protected.
- [ ] Sensitive paths blocked.
- [ ] Error messages do not expose secrets.

---

## 18. Safe use policy

This project is for lawful defensive use only:

- Protect your own website.
- Test only your own local firewall.
- Do not scan or attack other websites.
- Do not use logs to target others.
- Do not bypass security systems.

