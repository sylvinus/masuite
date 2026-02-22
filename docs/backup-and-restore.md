# Backup and Restore

## Creating a backup

```bash
./masuite backup
```

This creates a timestamped directory in `backups/`:

```
backups/2026-02-21_030000/
  docs_db.sql.gz
  meet_db.sql.gz
  drive_db.sql.gz
  messages_db.sql.gz
  projects_db.sql.gz
  conversations_db.sql.gz
  keycloak_realm.json
```

Only databases for enabled apps are backed up.

## What's backed up

- **PostgreSQL databases**: Full `pg_dump` for each app (compressed with gzip)
- **Keycloak realm**: Full realm export including users, clients, roles

## What's NOT backed up

- **Object storage (RustFS)**: File uploads in `data/objectstorage/` are not included in the automated backup. Back up this directory separately.
- **Redis**: Cache data, not critical to back up.

## Retention policy

Old backups are automatically cleaned up based on `.env` settings:

```
BACKUP_RETENTION_DAILY=7    # Keep 7 most recent backups
BACKUP_RETENTION_WEEKLY=4   # (not yet implemented)
```

## Restoring a database

To restore a single app's database:

```bash
gunzip -c backups/2026-02-21_030000/docs_db.sql.gz | \
  docker compose exec -T postgres psql -U masuite_app docs_db
```

## Full disaster recovery

1. Set up a fresh server and run `./masuite setup` with the same configuration
2. Start the stack: `./masuite start`
3. Stop the app you're restoring: `docker compose stop docs-backend docs-celery`
4. Drop and recreate the database, then restore from backup
5. Copy `data/objectstorage/` from your backup
6. Restart: `./masuite start`

## Recommended backup strategy

- Run `./masuite backup` daily via cron
- Copy `backups/` and `data/objectstorage/` to an off-site location (rsync, rclone, etc.)
- Test restores periodically
