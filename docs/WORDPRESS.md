# WordPress Protection Guide

Use this firewall as a reverse proxy in front of your WordPress site.

## Recommended blocked paths

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

## Do not block

Do not block these if you need normal WordPress use:

```text
/wp-admin
/wp-login.php
/wp-json
/wp-content
/wp-includes
```

## WordPress hardening

- Use strong admin password.
- Remove unused plugins.
- Update plugins/themes.
- Use trusted plugin/theme sources.
- Keep backups.
- Use HTTPS for public login.
- Do not expose database backups.
- Disable file editing in `wp-config.php` if possible:

```php
define('DISALLOW_FILE_EDIT', true);
```

## Uploads

If your WordPress site allows uploads:

- Keep upload limits reasonable.
- Do not allow PHP uploads.
- Validate MIME type.
- Rename files safely.
- Scan suspicious uploads.
