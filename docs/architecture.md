# Architecture

## Overview

MaSuite deploys up to 7 LaSuite apps behind a single reverse proxy, with shared infrastructure and unified authentication. Everything runs in Docker Compose on a single machine.

```
                        Internet
                           |
                        Caddy
                    (reverse proxy)
                    /    |    \     \
              Docs  Meet  Drive  Messages  Projects  Conversations
                \    |    /     /
              Keycloak (SSO)
              PostgreSQL
              Redis
              RustFS (S3)
```

## Infrastructure (always running)

| Service    | Image                | Purpose                        |
|------------|----------------------|--------------------------------|
| Caddy      | `caddy:2-alpine`     | Reverse proxy, TLS termination |
| PostgreSQL | `postgres:16-alpine` | Database for all apps          |
| Redis      | `redis:7-alpine`     | Cache, sessions, LiveKit       |
| RustFS     | `rustfs/rustfs`      | S3-compatible object storage   |
| Keycloak   | `quay.io/keycloak/keycloak` | SSO / OIDC provider     |

## Apps (controlled by profiles)

| App           | Stack                | Containers                                     |
|---------------|----------------------|------------------------------------------------|
| Docs          | Django + Next.js     | backend, frontend, celery, y-provider          |
| Meet          | Django + React/Vite  | backend, frontend, celery, LiveKit             |
| Drive         | Django + Next.js     | backend, frontend, celery, Collabora           |
| Messages      | Django + Next.js     | backend, frontend, celery, mta-in, mta-out, socks-proxy, OpenSearch, rspamd |
| Projects      | Sails.js (Node.js)   | single container (Planka fork)                 |
| Conversations | Django + Next.js     | backend, frontend                              |
| Calendars     | Django + Next.js     | backend, frontend, celery, CalDAV (SabreDAV)   |

## How app selection works

Docker Compose **profiles** control which apps start. Each app's services are tagged with a profile matching the app name:

```yaml
docs-backend:
  profiles: [docs]
```

The setup wizard writes the selected apps to `.env`:

```
COMPOSE_PROFILES=docs,meet,drive
```

`docker compose up` reads this and only starts services whose profile is listed. Infrastructure services have no profile, so they always run.

## Port assignments

| Port  | Service       |
|-------|---------------|
| 9120  | Homepage      |
| 9121  | Docs          |
| 9122  | Meet          |
| 9123  | Drive         |
| 9124  | Messages      |
| 9125  | Projects      |
| 9126  | Conversations |
| 9127  | Calendars     |
| 9200  | Keycloak      |
| 9201  | RustFS console|

In local mode, all ports are bound to `127.0.0.1`. In prod mode, Caddy listens on 80/443 and routes by subdomain.

## Modes

### Local mode
- HTTP only, `auto_https off` in Caddyfile
- URLs: `http://localhost:912x`
- Works fully offline after initial image pull

### Production mode
- HTTPS via Let's Encrypt (automatic)
- URLs: `https://subdomain.yourdomain.com`
- Subdomains: `docs.`, `meet.`, `drive.`, `mail.`, `projects.`, `chat.`, `cal.`, `auth.`, `livekit.`

## Authentication

All apps authenticate through a single Keycloak realm (`masuite`) using OIDC. A single shared client (`masuite`) is used for all apps, with one OIDC client secret (`SHARED_OIDC_CLIENT_SECRET`).

The dual-URL pattern handles Docker networking:
- **Browser** connects to Keycloak via the external URL (e.g. `http://localhost:9200`)
- **Backend** connects internally via `http://keycloak:8080`

Keycloak runs in production mode (`start`, not `start-dev`) so that `KC_HOSTNAME` is respected for token issuer validation.

## Object storage

RustFS provides S3-compatible storage for file uploads across all apps. Each app gets its own bucket (e.g. `docs-storage`, `drive-storage`). Bucket initialization uses the `minio/mc` client, which is compatible with RustFS.

For Docs and Drive, media requests go through Caddy's `forward_auth` directive, which checks authorization with the backend before proxying to RustFS.

## Database

A single PostgreSQL instance hosts per-app databases. The init script (`config/postgres/init-databases.sh`) creates a shared database user (`masuite_app`) with per-app databases, and installs required extensions (`pg_trgm`, `unaccent`).

All apps share one database user (`SHARED_DB_USER`, `SHARED_DB_PASSWORD`) with separate databases (`<APP>_DB_NAME`).

## Django settings overlays

The upstream Django apps ship with a `Production` settings class that hardcodes `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, etc. These are plain Python attributes, not `django-configurations` `values.Value()` descriptors, so they **cannot be overridden via environment variables**.

MaSuite provides settings overlay files (`config/settings/<app>_local.py`) that subclass the production config and override these attributes:

```python
class Local(Production):
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    LOGIN_REDIRECT_URL = "/"
```

This is set via `DJANGO_SETTINGS_MODULE=impress_local` + `DJANGO_CONFIGURATION=Local`. These overlays are a temporary workaround — upstream patches will eventually make them unnecessary.

## Service directory structure

All services (infrastructure and apps) live under `services/`:

```
services/
  _base/             # Shared infrastructure (always running)
    metadata.json    # Infra metadata (ports, subdomains, resource estimates)
    compose.yml      # PostgreSQL, Redis, RustFS, Keycloak, Caddy
    Caddyfile        # Caddy snippets for infra services
  <app>/             # Per-app service (controlled by profiles)
    metadata.json    # App metadata (loaded as APP_REGISTRY at runtime)
    compose.yml      # Docker Compose service definitions
    Caddyfile        # Caddy routing snippet
```

The CLI loads all `metadata.json` files to build a unified service registry (`SERVICE_REGISTRY`). Apps (everything except `_base`) are exposed as `APP_REGISTRY`. Infrastructure ports, subdomains, and resource estimates come from `_base/metadata.json` instead of being hardcoded.

The main Caddyfile imports all snippets via `import /etc/caddy/services/*/Caddyfile` and creates site blocks for enabled apps. See [Adding a New App](new_app.md) for details.

## Data-driven infrastructure

Several infrastructure resources are configured dynamically from the app registry:

- **PostgreSQL databases**: `APP_DB_NAMES` env var (space-separated list) drives the init script, so adding a new app doesn't require editing the postgres config.
- **S3 buckets**: `S3_BUCKETS` env var drives `rustfs-init`, so adding an app with S3 storage only requires setting `s3_bucket` in its metadata.json.
- **Caddy ports**: Port ranges (`9120-9129`, `9200-9209`) mean new apps don't require editing the Caddy port list.
