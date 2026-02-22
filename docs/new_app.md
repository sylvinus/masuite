# Adding a New App

Adding an app to MaSuite means creating a new directory in `services/` with 3 files:

```
services/<app>/
  metadata.json    # App metadata (name, port, subdomain, etc.)
  compose.yml      # Docker Compose services
  Caddyfile        # Caddy routing snippet
```

Everything else — `.env` variables, Keycloak client, PostgreSQL database, Django migrations, backups, and status display — is automatically derived from `metadata.json`.

## Step 1: Research the app

Before writing any config, understand the upstream app:

- **Stack**: Django? Node.js? What frontend?
- **Docker images**: Check Docker Hub (`lasuite/<app>-*`) and GHCR (`ghcr.io/suitenumerique/<app>-*`)
- **Containers needed**: backend, frontend, celery, any special services?
- **Environment variables**: DB, Redis, S3, OIDC — check the Django settings or docker-compose in the upstream repo
- **Settings module**: What's the `DJANGO_SETTINGS_MODULE` value? (e.g. `calendars.settings`)
- **Production class**: Does it hardcode `SECURE_SSL_REDIRECT=True`? (most LaSuite apps do)
- **Special dependencies**: CalDAV server, document editor, search engine, etc.
- **Architecture**: `amd64` only or multi-arch?

## Step 2: Create `metadata.json`

```json
{
  "label": "Calendars",
  "description": "Shared calendar (Google Calendar)",
  "port": 9127,
  "subdomain": "cal",
  "redis_db": 7,
  "default_enabled": false,
  "is_django": true,
  "settings_module": "calendars.settings",
  "settings_overlay": "calendars_local",
  "backend_service": "calendars-backend",
  "s3_bucket": null,
  "logo": null,
  "services": [
    "calendars-backend", "calendars-celery", "calendars-frontend",
    "calendars-caldav"
  ],
  "ram": 512,
  "vcpu": 0.5,
  "disk": 1024,
  "github": "https://github.com/suitenumerique/calendars"
}
```

This drives:
- Setup wizard app selection UI
- `.env` generation (URL, DB name, secret key, empty placeholders when disabled)
- `./masuite status` display grouping
- `./masuite backup` database inclusion
- `./masuite start` / `./masuite update` migration runner
- Website app listing and resource calculator (via `website/scripts/sync-apps.js`)

### Field reference

| Field | Type | Description |
|-------|------|-------------|
| `label` | str | Display name in UI |
| `description` | str | One-line description (shown in setup wizard) |
| `port` | int | Local mode port (912x range) |
| `subdomain` | str | Prod mode subdomain |
| `redis_db` | int/null | Redis DB number (unique per app, null if not used) |
| `default_enabled` | bool | Pre-selected in setup wizard |
| `is_django` | bool | Whether this is a Django app |
| `settings_module` | str/null | Django settings module (e.g. `impress.settings`) |
| `settings_overlay` | str/null | Name of settings overlay file (e.g. `impress_local`) |
| `backend_service` | str | Docker service name for the backend |
| `s3_bucket` | str/null | S3 bucket name (null if no S3 needed) |
| `logo` | str/null | URL for the Gaufre widget logo |
| `services` | list | All Docker service names for this app |
| `ram` | int | Estimated RAM usage in MB (used by website resource calculator) |
| `vcpu` | float | Estimated vCPU usage (used by website resource calculator) |
| `disk` | int | Estimated disk usage in MB (used by website resource calculator) |
| `github` | str | GitHub repository URL |

## Step 3: Create `compose.yml`

```yaml
services:

  calendars-backend:
    image: lasuite/calendars-backend:${CALENDARS_VERSION:-main}
    profiles: [calendars]
    restart: unless-stopped
    volumes:
      - ./config/settings/calendars_local.py:/app/calendars_local.py:ro
    environment:
      DJANGO_SETTINGS_MODULE: calendars_local
      DJANGO_CONFIGURATION: Local
      DJANGO_SECRET_KEY: ${CALENDARS_SECRET_KEY}
      DJANGO_ALLOWED_HOSTS: "*"
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_NAME: ${CALENDARS_DB_NAME}
      DB_USER: ${SHARED_DB_USER}
      DB_PASSWORD: ${SHARED_DB_PASSWORD}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/7
      # OIDC (shared client)
      OIDC_RP_CLIENT_ID: masuite
      OIDC_RP_CLIENT_SECRET: ${SHARED_OIDC_CLIENT_SECRET}
      OIDC_OP_AUTHORIZATION_ENDPOINT: ${KEYCLOAK_URL}/realms/masuite/protocol/openid-connect/auth
      OIDC_OP_TOKEN_ENDPOINT: http://keycloak:8080/realms/masuite/protocol/openid-connect/token
      OIDC_OP_JWKS_ENDPOINT: http://keycloak:8080/realms/masuite/protocol/openid-connect/certs
      OIDC_OP_USER_ENDPOINT: http://keycloak:8080/realms/masuite/protocol/openid-connect/userinfo
      OIDC_RP_SIGN_ALGO: RS256
      OIDC_RP_SCOPES: "openid email"
      # App-specific
      CALDAV_URL: http://calendars-caldav:80
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

Key points:
- **`profiles: [calendars]`** — matches the directory name
- **`DB_USER: ${SHARED_DB_USER}`** and **`DB_PASSWORD: ${SHARED_DB_PASSWORD}`** — shared credentials
- **`OIDC_RP_CLIENT_ID: masuite`** and **`OIDC_RP_CLIENT_SECRET: ${SHARED_OIDC_CLIENT_SECRET}`** — shared OIDC client
- **Unique Redis DB number** — must match `redis_db` in metadata.json
- **OIDC dual-URL pattern** — browser endpoints use `${KEYCLOAK_URL}`, backend endpoints use `http://keycloak:8080`
- **Settings overlay mount** — mount `config/settings/<overlay>.py` if the app is Django

## Step 4: Create `Caddyfile`

A Caddy snippet defining the app's routing:

```caddy
(calendars) {
	request_body {
		max_size 100MB
	}

	handle /rsvp/* {
		reverse_proxy calendars-backend:8000
	}

	handle /ical/* {
		reverse_proxy calendars-backend:8000
	}

	handle /api/* {
		reverse_proxy calendars-backend:8000
	}
	handle /admin/* {
		reverse_proxy calendars-backend:8000
	}
	handle /static/* {
		reverse_proxy calendars-backend:8000
	}

	handle {
		reverse_proxy calendars-frontend:8080
	}
}
```

The snippet name must match the directory name. The site address (`:9127` or `cal.example.com`) is added by the generated main Caddyfile.

## Step 5: Wire it up

Include the compose file in `docker-compose.yml`:

```yaml
include:
  - path: services/calendars/compose.yml
    project_directory: .
```

No other changes needed for infrastructure:
- **Caddy ports**: The base compose uses port ranges (`9120-9129`), so new ports within the range work automatically.
- **S3 buckets**: Set `s3_bucket` in `metadata.json` and the setup wizard generates the `S3_BUCKETS` env var for `rustfs-init`.
- **PostgreSQL database**: The setup wizard generates the `APP_DB_NAMES` env var for the init script.

## Step 6: Optional extras

### Settings overlay

If the app is Django and uses `SECURE_SSL_REDIRECT=True` in production settings, add a settings overlay in `config/settings/<overlay>.py`:

```python
"""Local mode settings overlay - disables HTTPS requirements."""
from calendars.settings import *  # noqa: F401,F403
from calendars.settings import Production as _Production

class Local(_Production):
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    LOGIN_REDIRECT_URL = "/"
```

### App-specific `.env` variables

If the app needs special config beyond the standard set, add a conditional block in `build_env()` in `cli/setup_wizard.py`:

```python
if "calendars" in enabled:
    w("# Calendars - CalDAV")
    w(f"CALENDARS_CALDAV_INBOUND_API_KEY={keep('CALENDARS_CALDAV_INBOUND_API_KEY', generate_secret(32))}")
    w()
```

### Image version

Pin the version in `versions.env`:

```
CALENDARS_VERSION=main
```

## Checklist

- [ ] `services/<app>/metadata.json` — app metadata (drives everything else)
- [ ] `services/<app>/compose.yml` — Docker service definitions
- [ ] `services/<app>/Caddyfile` — Caddy routing snippet
- [ ] `docker-compose.yml` — include the compose file
- [ ] `config/settings/<overlay>.py` — settings overlay (if Django)
- [ ] `versions.env` — image version pin
