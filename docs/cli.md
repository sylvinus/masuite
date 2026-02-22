# CLI Reference

MaSuite is operated via the `./masuite` wrapper script, which calls into a pure Python CLI (no external dependencies).

## Commands

### `setup`

Run the interactive setup wizard. Generates `.env`, Caddyfile, and homepage config.

```bash
./masuite setup
./masuite setup --mode local --apps docs,meet,drive
./masuite setup --mode prod --apps docs,meet,drive,messages,projects,conversations
```

| Flag | Description |
|------|-------------|
| `--apps` | Comma-separated list of apps to enable |
| `--mode` | `local` or `prod` |

### `start`

Start all enabled services and configure Keycloak (set OIDC client secret and redirect URIs).

```bash
./masuite start
```

### `stop`

Stop all services.

```bash
./masuite stop
```

### `restart`

Stop then start all services.

```bash
./masuite restart
```

### `status`

Show running containers.

```bash
./masuite status
```

### `logs`

Tail logs for all services or a specific one.

```bash
./masuite logs
./masuite logs docs-backend
```

### `update`

Pull latest code and images, recreate containers, run migrations.

```bash
./masuite update
```

This runs:
1. `git pull --ff-only`
2. `docker compose pull`
3. `docker compose up -d --remove-orphans`
4. Django migrations for each enabled app

### `backup`

Dump all databases and export the Keycloak realm.

```bash
./masuite backup
```

Backups are stored in `backups/YYYY-MM-DD_HHMMSS/` with:
- `<app>_db.sql.gz` for each enabled app
- `keycloak_realm.json`

Old backups are cleaned up based on `BACKUP_RETENTION_DAILY` (default: 7).

### `user create`

Create a user in Keycloak.

```bash
./masuite user create alice@example.com
./masuite user create alice@example.com --password mysecretpassword
```

### `user list`

List all users.

```bash
./masuite user list
```

## Generated files

The `setup` command generates:

| File | Purpose |
|------|---------|
| `.env` | All secrets and configuration |
| `config/caddy/Caddyfile` | Reverse proxy stub (imports per-app snippets) |
| `config/homepage/config.json` | Homepage app listing |
| `config/homepage/gaufre-services.json` | Gaufre widget services |
| `config/livekit/livekit.yaml` | LiveKit config (if Meet enabled) |
| `config/docs-theme.json` | Docs theme customization (if Docs enabled) |

Static files (committed, not generated):

| File | Purpose |
|------|---------|
| `services/_base/metadata.json` | Infrastructure metadata (ports, subdomains, resources) |
| `services/_base/compose.yml` | Infrastructure Docker services |
| `services/_base/Caddyfile` | Caddy snippets for infra services |
| `services/<app>/metadata.json` | App metadata (loaded as APP_REGISTRY) |
| `services/<app>/compose.yml` | App Docker services |
| `services/<app>/Caddyfile` | Caddy routing snippet |
| `config/keycloak/masuite-realm.json` | OIDC realm definition |
| `config/settings/<app>_local.py` | Django settings overlays |
