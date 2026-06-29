# Hardening Examples

Copy the settings you need into `config.yml`.

## Strict small website

```yml
max_body_bytes: 1048576
rate_limit_requests: 30
rate_limit_seconds: 60
```

## Upload website

```yml
max_body_bytes: 209715200
rate_limit_requests: 120
rate_limit_seconds: 60
```

Also protect your backend upload handler. This firewall only checks HTTP traffic before the backend.

## WordPress recommended blocked paths

```yml
blocked_paths:
  - "/.env"
  - "/wp-config.php"
  - "/xmlrpc.php"
  - "/readme.html"
  - "/license.txt"
  - "/backup.zip"
  - "/database.sql"
  - "/phpmyadmin"
  - "/wp-admin/install.php"
  - "/wp-admin/setup-config.php"
```

## Extra custom rules

```yml
custom_block_regex:
  - "(?i)\\.git"
  - "(?i)\\.svn"
  - "(?i)id_rsa"
  - "(?i)composer\\.json"
  - "(?i)composer\\.lock"
  - "(?i)package-lock\\.json"
  - "(?i)yarn\\.lock"
  - "(?i)\\.sql(\\?|$)"
  - "(?i)backup.*\\.zip"
```

## Reduce false positives

If normal users are blocked:

1. Check `logs/blocked.log`.
2. Identify the rule name in `reason`.
3. Disable only the problem module temporarily.
4. Create a better custom allow or backend route.
5. Re-enable protection after testing.

Avoid adding too many IPs to `allowed_ips.txt`, because allowed IPs bypass rule checks.
