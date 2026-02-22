"""Rich status display for MaSuite services."""

import json
import os
import shutil
import subprocess

from .setup_wizard import SERVICE_REGISTRY, APP_REGISTRY


def _build_service_groups():
    """Derive service groups from SERVICE_REGISTRY."""
    groups = {}
    for svc_id, svc in SERVICE_REGISTRY.items():
        groups[svc["label"]] = list(svc["services"])
    return groups


SERVICE_GROUPS = _build_service_groups()


def _fmt_bytes(n):
    """Format bytes as human-readable string."""
    if n < 0:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _parse_docker_size(s):
    """Parse docker stats memory/size string like '123.4MiB' to bytes."""
    s = s.strip()
    units = {"B": 1, "KIB": 1024, "MIB": 1024**2, "GIB": 1024**3, "TIB": 1024**4,
             "KB": 1000, "MB": 1000**2, "GB": 1000**3, "TB": 1000**4}
    for suffix, mult in sorted(units.items(), key=lambda x: -len(x[0])):
        if s.upper().endswith(suffix):
            try:
                return float(s[:len(s)-len(suffix)].strip()) * mult
            except ValueError:
                return -1
    try:
        return float(s)
    except ValueError:
        return -1


def run(root_dir, compose_cmd):
    """Display comprehensive status information."""

    # 1. Get container list with status
    result = subprocess.run(
        [*compose_cmd, "ps", "--format", "json", "-a"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("Failed to get container status.")
        return

    containers = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            containers.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not containers:
        print("No containers found. Run ./masuite start first.")
        return

    # 2. Get resource stats (CPU, memory) for running containers
    running_names = [c["Name"] for c in containers if c.get("State") == "running"]
    stats = {}
    if running_names:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format",
             "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}",
             *running_names],
            capture_output=True, text=True,
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 4:
                name = parts[0]
                stats[name] = {
                    "cpu": parts[1],
                    "mem_usage": parts[2].split("/")[0].strip(),
                    "mem_pct": parts[3],
                }

    # 3. Build service name -> container info map
    svc_map = {}
    for c in containers:
        svc = c.get("Service", c.get("Name", ""))
        svc_map[svc] = c

    # 4. Read URLs from .env
    env_path = os.path.join(root_dir, ".env")
    env_vars = {}
    profiles = set()
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env_vars[k.strip()] = v.strip()
        profiles = {p.strip() for p in env_vars.get("COMPOSE_PROFILES", "").split(",")}

    mode = env_vars.get("MASUITE_MODE", "unknown")

    # 5. Print header
    print()
    print("  MaSuite Status")
    print("  " + "=" * 60)
    print(f"  Mode: {mode}    Apps: {', '.join(sorted(profiles))}")
    print()

    # 6. Print service table grouped by app
    total_mem = 0
    total_cpu = 0.0

    header = f"  {'Service':<28} {'Status':<12} {'CPU':>7} {'Memory':>10}"
    print(header)
    print("  " + "-" * 60)

    for group_name, services in SERVICE_GROUPS.items():
        # Check if any service in this group is present
        group_services = [(s, svc_map.get(s)) for s in services if s in svc_map]
        if not group_services:
            continue

        print(f"  {group_name}")
        for svc_name, c in group_services:
            if c is None:
                continue
            state = c.get("State", "unknown")
            health = c.get("Health", "")

            # Format status with health
            if state == "running":
                if health == "healthy":
                    status_str = "healthy"
                elif health == "unhealthy":
                    status_str = "unhealthy"
                else:
                    status_str = "running"
            elif state == "exited":
                exit_code = c.get("ExitCode", "?")
                status_str = f"exited({exit_code})"
            else:
                status_str = state

            # Get stats
            container_name = c.get("Name", "")
            s = stats.get(container_name, {})
            cpu_str = s.get("cpu", "-")
            mem_str = s.get("mem_usage", "-")

            # Accumulate totals
            if cpu_str != "-":
                try:
                    total_cpu += float(cpu_str.replace("%", ""))
                except ValueError:
                    pass
            if mem_str != "-":
                total_mem += _parse_docker_size(mem_str)

            # Short name: strip "masuite-" prefix and "-1" suffix
            short = svc_name

            print(f"    {short:<26} {status_str:<12} {cpu_str:>7} {mem_str:>10}")

    # 7. Totals
    print("  " + "-" * 60)
    print(f"  {'Total':<28} {'':<12} {total_cpu:>6.1f}% {_fmt_bytes(total_mem):>10}")
    print()

    # 8. Disk usage
    data_dir = os.path.join(root_dir, "data")
    if os.path.isdir(data_dir):
        print("  Disk usage (data/):")
        subdirs = []
        try:
            for name in sorted(os.listdir(data_dir)):
                path = os.path.join(data_dir, name)
                if os.path.isdir(path):
                    # Use du for accurate directory size
                    r = subprocess.run(
                        ["du", "-sb", path], capture_output=True, text=True,
                    )
                    if r.returncode == 0:
                        size = int(r.stdout.split()[0])
                        subdirs.append((name, size))
        except OSError:
            pass

        total_disk = sum(s for _, s in subdirs)
        for name, size in subdirs:
            bar_len = int(30 * size / total_disk) if total_disk > 0 else 0
            bar = "#" * bar_len
            print(f"    {name:<20} {_fmt_bytes(size):>10}  {bar}")
        print(f"    {'Total':<20} {_fmt_bytes(total_disk):>10}")
        print()

    # 9. Overall disk free
    disk = shutil.disk_usage(root_dir)
    used_pct = disk.used / disk.total * 100
    print(f"  System disk: {_fmt_bytes(disk.used)} / {_fmt_bytes(disk.total)} ({used_pct:.0f}% used)")

    # 10. URLs (derived from registry)
    url_entries = [("Homepage", "HOMEPAGE_URL")]
    for app_id, app in APP_REGISTRY.items():
        url_entries.append((app["label"], f"{app_id.upper()}_URL"))
    url_entries.append(("Keycloak", "KEYCLOAK_URL"))

    urls = [(label, env_vars[key]) for label, key in url_entries
            if key in env_vars and env_vars[key]]
    if urls:
        print()
        print("  URLs:")
        for label, url in urls:
            print(f"    {label:<16} {url}")

    print()
