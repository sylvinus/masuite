# Troubleshooting

## Check service status

```bash
./masuite status
./masuite logs              # all services
./masuite logs docs-backend # specific service
```

## Common issues

### OIDC login fails with "invalid issuer"

Keycloak must run in production mode (`start`, not `start-dev`) for `KC_HOSTNAME` to be respected. Check that `keycloak` in `docker-compose.yml` has `command: start --import-realm`.

### OIDC login redirects to HTTPS but you're running locally

The upstream Django `Production` settings class hardcodes `SECURE_SSL_REDIRECT=True`. Make sure:
- `DJANGO_SETTINGS_MODULE` points to the local overlay (e.g. `impress_local`, not `impress.settings`)
- `DJANGO_CONFIGURATION` is `Local`
- The settings file is mounted at `/app/<name>_local.py`

### Messages: users can't log in

`OIDC_CREATE_USER` defaults to `False` in Messages. Ensure `OIDC_CREATE_USER=True` is set in the environment.

### Projects: user names show as empty

Planka defaults to France Connect attributes (`given_name`, `usual_name`). For standard Keycloak, set:
```
OIDC_FULLNAME_ATTRIBUTES=given_name,family_name
```

### Docs migration fails on `unaccent`

The `unaccent` extension requires SUPERUSER privileges. The init script grants SUPERUSER to the shared app database user. If you created databases manually, run:

```sql
ALTER USER masuite_app WITH SUPERUSER;
```

### Containers can't resolve each other

Docker Compose networking should handle this automatically. If using Caddy with upstream names, ensure the service names match what's in the Caddyfile.

### Port conflicts

All ports are in the 9120-9201 range. Check for conflicts:

```bash
ss -tlnp | grep '912\|920'
```

### "permission denied" on data directories

Some containers run as non-root. If volumes have wrong ownership:

```bash
docker compose exec -u root docs-backend chown -R 1000:1000 /data
```

For migrations specifically:

```bash
docker compose exec -u root docs-backend python manage.py migrate
```

### arm64 compatibility

Only Docs and Meet have multi-arch images. Drive, Projects, Conversations, and Messages are `amd64` only. On ARM machines (Apple Silicon, Ampere), these will run under QEMU emulation, which is slower and may cause uvicorn worker crashes.

## Resetting everything

To start fresh (destroys all data):

```bash
./masuite stop
rm -rf data/ .env config/caddy/Caddyfile config/keycloak/masuite-realm.json config/homepage/index.html
./masuite setup
./masuite start
```
