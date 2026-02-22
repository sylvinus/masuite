"""Backup management for MaSuite."""

import os
import subprocess
import datetime


def _load_env(root_dir):
    """Load .env file as a dict."""
    env = {}
    env_path = os.path.join(root_dir, ".env")
    if not os.path.exists(env_path):
        return env
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def _compose_cmd(root_dir):
    return ["docker", "compose", "--project-directory", root_dir]


def run(root_dir):
    """Run a backup of all databases and S3 buckets."""
    env = _load_env(root_dir)
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_dir = os.path.join(root_dir, "backups", now)
    os.makedirs(backup_dir, exist_ok=True)

    print(f"Backing up to {backup_dir}/")

    # PostgreSQL: dump each app database
    from .setup_wizard import APP_REGISTRY
    apps = [a.strip() for a in env.get("COMPOSE_PROFILES", "").split(",") if a.strip()]
    db_user = env.get("SHARED_DB_USER", "masuite_app")

    for app in apps:
        if app not in APP_REGISTRY:
            continue
        db_name = env.get(f"{app.upper()}_DB_NAME")
        if not db_name:
            continue

        dump_file = os.path.join(backup_dir, f"{app}_db.sql.gz")
        print(f"  Dumping {db_name}...", end=" ", flush=True)

        result = subprocess.run(
            [
                *_compose_cmd(root_dir),
                "exec", "-T", "postgres",
                "pg_dump", "-U", db_user, db_name,
            ],
            capture_output=True,
        )

        if result.returncode == 0:
            import gzip
            with gzip.open(dump_file, "wb") as f:
                f.write(result.stdout)
            size_mb = os.path.getsize(dump_file) / (1024 * 1024)
            print(f"done ({size_mb:.1f} MB)")
        else:
            print(f"FAILED: {result.stderr.decode()[:200]}")

    # Keycloak realm export
    print("  Exporting Keycloak realm...", end=" ", flush=True)
    result = subprocess.run(
        [
            *_compose_cmd(root_dir),
            "exec", "-T", "keycloak",
            "/opt/keycloak/bin/kc.sh", "export",
            "--realm", "masuite",
            "--file", "/tmp/masuite-realm-export.json",
        ],
        capture_output=True,
    )

    if result.returncode == 0:
        # Copy the export out of the container
        subprocess.run(
            [
                *_compose_cmd(root_dir),
                "cp", "keycloak:/tmp/masuite-realm-export.json",
                os.path.join(backup_dir, "keycloak_realm.json"),
            ],
            capture_output=True,
        )
        print("done")
    else:
        print(f"FAILED: {result.stderr.decode()[:200]}")

    # Cleanup old backups
    _cleanup_old_backups(root_dir, env)

    print(f"\nBackup complete: {backup_dir}/")


def _cleanup_old_backups(root_dir, env):
    """Remove backups older than retention policy."""
    backup_root = os.path.join(root_dir, "backups")
    if not os.path.exists(backup_root):
        return

    daily = int(env.get("BACKUP_RETENTION_DAILY", "7"))
    # List all backup dirs sorted by name (date)
    dirs = sorted(
        [d for d in os.listdir(backup_root)
         if os.path.isdir(os.path.join(backup_root, d))],
        reverse=True,
    )

    # Keep the most recent N daily backups
    to_remove = dirs[daily:]
    for d in to_remove:
        path = os.path.join(backup_root, d)
        import shutil
        shutil.rmtree(path, ignore_errors=True)
        print(f"  Removed old backup: {d}")
