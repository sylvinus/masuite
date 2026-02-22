"""Update MaSuite: pull code, images, and restart."""

import os
import subprocess
import sys


def _compose_cmd(root_dir):
    return ["docker", "compose", "--project-directory", root_dir]


def run(root_dir):
    """Pull latest code and images, then restart."""

    # 1. Git pull
    print("Pulling latest code...", end=" ", flush=True)
    result = subprocess.run(
        ["git", "-C", root_dir, "pull", "--ff-only"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("done")
        if "Already up to date" not in result.stdout:
            print(f"  {result.stdout.strip()}")
    else:
        print(f"FAILED\n  {result.stderr.strip()}")
        print("  Try: git -C", root_dir, "status")
        sys.exit(1)

    # 2. Pull new images
    print("Pulling Docker images...", end=" ", flush=True)
    result = subprocess.run(
        [*_compose_cmd(root_dir), "pull"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("done")
    else:
        print(f"FAILED\n  {result.stderr.strip()}")
        sys.exit(1)

    # 3. Recreate containers
    print("Restarting services...", end=" ", flush=True)
    result = subprocess.run(
        [*_compose_cmd(root_dir), "up", "-d", "--remove-orphans"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("done")
    else:
        print(f"FAILED\n  {result.stderr.strip()}")
        sys.exit(1)

    # 4. Run Django migrations for enabled apps
    _run_migrations(root_dir)

    print("\nUpdate complete.")


def _run_migrations(root_dir):
    """Run Django migrate for each enabled Django app."""
    from .setup_wizard import APP_REGISTRY
    django_apps = {
        k: v["backend_service"]
        for k, v in APP_REGISTRY.items() if v["is_django"]
    }

    # Read COMPOSE_PROFILES from .env
    env_path = os.path.join(root_dir, ".env")
    profiles = set()
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("COMPOSE_PROFILES="):
                    profiles = {p.strip() for p in line.split("=", 1)[1].strip().split(",")}

    for app_id, service_name in django_apps.items():
        if app_id not in profiles:
            continue
        print(f"  Running migrations for {app_id}...", end=" ", flush=True)
        result = subprocess.run(
            [*_compose_cmd(root_dir), "exec", "-T", "-u", "root", service_name,
             "python", "manage.py", "migrate", "--noinput"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("done")
        else:
            print(f"WARNING: {result.stderr.strip()[:200]}")
