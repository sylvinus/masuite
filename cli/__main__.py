"""MaSuite CLI - Self-hosted La Suite Numerique."""

import argparse
import os
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_compose_cmd():
    return ["docker", "compose", "--project-directory", ROOT_DIR]


def _require_env():
    """Check that .env exists. Exit with helpful message if not."""
    env_path = os.path.join(ROOT_DIR, ".env")
    if not os.path.exists(env_path):
        print("No configuration found. Run ./masuite setup first.")
        sys.exit(1)


def cmd_setup(args):
    from . import setup_wizard
    setup_wizard.run(ROOT_DIR, preset_apps=args.apps, preset_mode=args.mode)


def cmd_start(args):
    _require_env()
    from . import docker_utils
    docker_utils.require_docker()
    subprocess.run([*get_compose_cmd(), "up", "-d"], check=True)
    # Run Django migrations for each enabled app
    _run_migrations()
    # Configure Keycloak OIDC clients (sets secrets + protocol mappers)
    from . import keycloak_setup
    keycloak_setup.configure(ROOT_DIR)


def _run_migrations():
    """Run Django migrations for each enabled app after start."""
    from .setup_wizard import APP_REGISTRY
    django_services = {
        k: v["backend_service"]
        for k, v in APP_REGISTRY.items() if v["is_django"]
    }

    # Read enabled apps from .env
    env_path = os.path.join(ROOT_DIR, ".env")
    profiles = set()
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("COMPOSE_PROFILES="):
                    profiles = {p.strip() for p in line.split("=", 1)[1].strip().split(",")}

    ran_any = False
    for app_id, service in django_services.items():
        if app_id not in profiles:
            continue
        if not ran_any:
            print("Running migrations...", flush=True)
            ran_any = True
        print(f"  {app_id}...", end=" ", flush=True)
        result = subprocess.run(
            [*get_compose_cmd(), "exec", "-T", "-u", "root", service,
             "python", "manage.py", "migrate", "--noinput"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("done")
        else:
            # Show a brief error but don't abort
            err = result.stderr.strip()[-200:] if result.stderr else "unknown error"
            print(f"WARNING: {err}")


def cmd_stop(args):
    _require_env()
    from . import docker_utils
    docker_utils.require_docker()
    subprocess.run([*get_compose_cmd(), "down"], check=True)


def cmd_restart(args):
    cmd_stop(args)
    cmd_start(args)


def cmd_update(args):
    _require_env()
    from . import docker_utils
    docker_utils.require_docker()
    from . import update
    update.run(ROOT_DIR)


def cmd_backup(args):
    _require_env()
    from . import docker_utils
    docker_utils.require_docker()
    from . import backup
    backup.run(ROOT_DIR)


def cmd_status(args):
    _require_env()
    from . import docker_utils
    docker_utils.require_docker()
    from . import status
    status.run(ROOT_DIR, get_compose_cmd())


def cmd_logs(args):
    _require_env()
    from . import docker_utils
    docker_utils.require_docker()
    cmd = [*get_compose_cmd(), "logs", "--tail=100", "-f"]
    if args.service:
        cmd.append(args.service)
    subprocess.run(cmd)


def cmd_user(args):
    _require_env()
    from . import docker_utils
    docker_utils.require_docker()
    from . import user
    if args.user_action == "create":
        user.create(ROOT_DIR, args.email, args.password)
    elif args.user_action == "list":
        user.list_users(ROOT_DIR)


def main():
    parser = argparse.ArgumentParser(
        prog="masuite",
        description="MaSuite - Self-hosted La Suite Numerique",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    setup_parser = sub.add_parser("setup", help="Interactive setup wizard")
    setup_parser.add_argument("--apps", help="Comma-separated list of apps to enable (e.g. docs,meet,drive)")
    setup_parser.add_argument("--mode", choices=["local", "prod"], help="Deployment mode")
    sub.add_parser("start", help="Start all enabled services")
    sub.add_parser("stop", help="Stop all services")
    sub.add_parser("restart", help="Restart all services")
    sub.add_parser("update", help="Pull updates and restart")
    sub.add_parser("backup", help="Run backup now")
    sub.add_parser("status", help="Show service status")

    logs_parser = sub.add_parser("logs", help="Tail service logs")
    logs_parser.add_argument("service", nargs="?", help="Service name (optional)")

    user_parser = sub.add_parser("user", help="Manage users")
    user_sub = user_parser.add_subparsers(dest="user_action", required=True)
    create_parser = user_sub.add_parser("create", help="Create a user")
    create_parser.add_argument("email", help="User email")
    create_parser.add_argument("--password", help="Password (generated if omitted)")
    user_sub.add_parser("list", help="List users")

    args = parser.parse_args()
    cmd_map = {
        "setup": cmd_setup,
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "update": cmd_update,
        "backup": cmd_backup,
        "status": cmd_status,
        "logs": cmd_logs,
        "user": cmd_user,
    }
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
