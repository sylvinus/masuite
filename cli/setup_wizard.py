"""Interactive setup wizard for MaSuite."""

import json
import os
import secrets
import string

# ──────────────────────────────────────────────────────────────────────
# Service Registry - loaded from services/*/metadata.json at import time.
# SERVICE_REGISTRY: all services (including _base infrastructure)
# APP_REGISTRY:     user-selectable apps only (excludes infrastructure)
# ──────────────────────────────────────────────────────────────────────

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_service_registry():
    """Load all service metadata from services/*/metadata.json files."""
    registry = {}
    services_dir = os.path.join(_PROJECT_ROOT, "services")
    if not os.path.isdir(services_dir):
        return registry
    for entry in sorted(os.listdir(services_dir)):
        meta_path = os.path.join(services_dir, entry, "metadata.json")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                registry[entry] = json.load(f)
    return registry


SERVICE_REGISTRY = _load_service_registry()
APP_REGISTRY = {k: v for k, v in SERVICE_REGISTRY.items() if not v.get("is_infrastructure")}

# ── Derived views ─────────────────────────────────────────────────────

_INFRA = SERVICE_REGISTRY.get("_base", {})

APPS = [(k, v["label"], v["description"]) for k, v in APP_REGISTRY.items()]
DEFAULT_APPS = {k for k, v in APP_REGISTRY.items() if v["default_enabled"]}

# Unified port map: infra ports (homepage, keycloak, rustfs_console) + app ports
APP_PORTS = {
    **_INFRA.get("ports", {}),
    **{k: v["port"] for k, v in APP_REGISTRY.items()},
}

# Unified subdomain map: infra subdomains (homepage, keycloak, rustfs, livekit) + app subdomains
APP_SUBDOMAINS = {
    **_INFRA.get("subdomains", {}),
    **{k: v["subdomain"] for k, v in APP_REGISTRY.items()},
}

GAUFRE_SCRIPT_URL = "https://static.suite.anct.gouv.fr/widgets/"

APP_LOGOS = {k: v["logo"] for k, v in APP_REGISTRY.items() if v.get("logo")}


def ask(prompt, default=None):
    """Ask a question with optional default."""
    if default:
        prompt = f"{prompt} [{default}]"
    prompt = f"{prompt}: "
    value = input(prompt).strip()
    return value if value else default


def ask_yn(prompt, default=True):
    """Ask a yes/no question."""
    hint = "Y/n" if default else "y/N"
    answer = ask(prompt, hint)
    if answer in ("Y/n", "y/N"):
        return default
    return answer.lower().startswith("y")


def generate_secret(length=48):
    """Generate a URL-safe random secret."""
    return secrets.token_urlsafe(length)


def generate_password(length=24):
    """Generate a readable random password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_fernet_key():
    """Generate a Fernet-compatible key (base64, 32 bytes)."""
    import base64
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()


def _load_existing_env(root_dir):
    """Load existing .env values to preserve secrets on re-run."""
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


def build_env(config):
    """Build the .env file contents from config dict.

    Preserves existing secrets from prior .env when re-running setup.
    """
    # Load existing env to preserve secrets
    existing = _load_existing_env(config.get("root_dir", ""))

    def keep(key, new_value):
        """Return existing value if present, else new_value."""
        return existing.get(key, new_value)

    lines = []

    def w(line=""):
        lines.append(line)

    mode = config["mode"]
    domain = config.get("domain", "")
    enabled = config["enabled_apps"]

    # Compose profiles
    profiles = list(enabled)
    w(f'COMPOSE_PROFILES={",".join(sorted(profiles))}')
    w()

    # Mode and domain
    w(f"MASUITE_MODE={mode}")
    w(f"BASE_DOMAIN={domain}")
    w()

    # App URLs
    w("# App URLs")
    for app_id, app in APP_REGISTRY.items():
        if app_id not in enabled:
            continue
        if mode == "local":
            w(f"{app_id.upper()}_URL=http://localhost:{app['port']}")
        else:
            w(f"{app_id.upper()}_URL=https://{app['subdomain']}.{domain}")
    w()

    # Homepage URL
    if mode == "local":
        w(f"HOMEPAGE_URL=http://localhost:{APP_PORTS['homepage']}")
    else:
        subdomain = APP_SUBDOMAINS["homepage"]
        if subdomain:
            w(f"HOMEPAGE_URL=https://{subdomain}.{domain}")
        else:
            w(f"HOMEPAGE_URL=https://{domain}")
    w()

    # Gaufre (app navigation widget)
    w("# Gaufre - app navigation widget")
    if mode == "local":
        w(f"GAUFRE_SERVICES_URL=http://localhost:{APP_PORTS['homepage']}/gaufre-services.json")
    else:
        subdomain = APP_SUBDOMAINS["homepage"]
        w(f"GAUFRE_SERVICES_URL=https://{subdomain}.{domain}/gaufre-services.json")
    w(f"GAUFRE_SCRIPT_URL={GAUFRE_SCRIPT_URL}")
    w()

    # Keycloak
    w("# Keycloak")
    if mode == "local":
        w(f"KEYCLOAK_URL=http://localhost:{APP_PORTS['keycloak']}")
    else:
        w(f"KEYCLOAK_URL=https://{APP_SUBDOMAINS['keycloak']}.{domain}")
    w(f"KEYCLOAK_ADMIN_USER=admin")
    w(f'KEYCLOAK_ADMIN_PASSWORD={config["keycloak_admin_password"]}')
    w(f"KEYCLOAK_DB_PASSWORD={keep('KEYCLOAK_DB_PASSWORD', generate_secret(32))}")
    w()

    # Database (shared user for all apps)
    w("# PostgreSQL")
    w(f"POSTGRES_ADMIN_PASSWORD={keep('POSTGRES_ADMIN_PASSWORD', generate_secret(32))}")
    w(f"SHARED_DB_USER={keep('SHARED_DB_USER', 'masuite_app')}")
    w(f"SHARED_DB_PASSWORD={keep('SHARED_DB_PASSWORD', generate_secret(32))}")
    # Per-app DB names (used by individual app compose files)
    for app_id in enabled:
        w(f"{app_id.upper()}_DB_NAME={app_id}_db")
    # Consolidated list for postgres init script
    db_names = " ".join(f"{app_id}_db" for app_id in sorted(enabled))
    w(f"APP_DB_NAMES={db_names}")
    w()

    # Redis
    w("# Redis")
    w(f"REDIS_PASSWORD={keep('REDIS_PASSWORD', generate_secret(32))}")
    w()

    # RustFS (S3-compatible storage)
    w("# RustFS (S3)")
    w(f"RUSTFS_ACCESS_KEY={keep('RUSTFS_ACCESS_KEY', 'masuite')}")
    w(f"RUSTFS_SECRET_KEY={keep('RUSTFS_SECRET_KEY', generate_secret(32))}")
    if mode == "prod":
        w(f"S3_URL=https://{APP_SUBDOMAINS['rustfs']}.{domain}")
    # In local mode, S3_URL is not set; compose falls back to http://rustfs:9000
    # Consolidated bucket list for rustfs-init
    buckets = " ".join(
        APP_REGISTRY[app_id]["s3_bucket"]
        for app_id in sorted(enabled)
        if APP_REGISTRY[app_id].get("s3_bucket")
    )
    w(f"S3_BUCKETS={buckets}")
    w()

    # Per-app secrets
    w("# App secrets")
    for app_id in enabled:
        prefix = app_id.upper()
        w(f"{prefix}_SECRET_KEY={keep(f'{prefix}_SECRET_KEY', generate_secret())}")
    w()

    # Single OIDC client secret
    w("# OIDC client secret (Keycloak)")
    w(f"SHARED_OIDC_CLIENT_SECRET={keep('SHARED_OIDC_CLIENT_SECRET', generate_secret(32))}")
    w()

    # App-specific config
    if "meet" in enabled:
        w("# LiveKit")
        w(f"LIVEKIT_API_KEY={keep('LIVEKIT_API_KEY', f'masuite_{generate_secret(8)}')}")
        w(f"LIVEKIT_API_SECRET={keep('LIVEKIT_API_SECRET', generate_secret(32))}")
        if mode == "local":
            w("LIVEKIT_URL=ws://localhost:7880")
        else:
            subdomain = APP_SUBDOMAINS["livekit"]
            w(f"LIVEKIT_URL=wss://{subdomain}.{domain}")
        w()

    if "drive" in enabled:
        w("# Drive - Document editor")
        editor = config.get("drive_editor", "collabora")
        w(f"DRIVE_EDITOR={editor}")
        w()

    if "conversations" in enabled:
        w("# Conversations - LLM")
        w(f'CONVERSATIONS_LLM_BACKEND={config.get("llm_backend", "")}')
        w(f'CONVERSATIONS_LLM_API_KEY={config.get("llm_api_key", "")}')
        w(f'CONVERSATIONS_LLM_MODEL={config.get("llm_model", "")}')
        w()

    if "messages" in enabled:
        w("# Messages - SMTP")
        w(f'MESSAGES_MAIL_DOMAIN={config.get("mail_domain", domain)}')
        w(f'MESSAGES_SMTP_RELAY_HOST={config.get("smtp_relay_host", "")}')
        w(f'MESSAGES_SMTP_RELAY_USER={config.get("smtp_relay_user", "")}')
        w(f'MESSAGES_SMTP_RELAY_PASSWORD={config.get("smtp_relay_password", "")}')
        w()

    if "calendars" in enabled:
        w("# Calendars - CalDAV")
        w(f"CALENDARS_CALDAV_INBOUND_API_KEY={keep('CALENDARS_CALDAV_INBOUND_API_KEY', generate_secret(32))}")
        w(f"CALENDARS_CALDAV_OUTBOUND_API_KEY={keep('CALENDARS_CALDAV_OUTBOUND_API_KEY', generate_secret(32))}")
        w()

    # Empty values for disabled apps (prevents docker-compose warnings
    # about unset variables in inactive profile services)
    disabled = set(APP_REGISTRY.keys()) - enabled
    if disabled:
        for app_id in sorted(disabled):
            prefix = app_id.upper()
            w(f"{prefix}_URL=")
            w(f"{prefix}_DB_NAME=")
            w(f"{prefix}_SECRET_KEY=")
        if "meet" not in enabled:
            w("LIVEKIT_API_KEY=")
            w("LIVEKIT_API_SECRET=")
            w("LIVEKIT_URL=")
        if "calendars" not in enabled:
            w("CALENDARS_CALDAV_INBOUND_API_KEY=")
            w("CALENDARS_CALDAV_OUTBOUND_API_KEY=")
        w()

    # Backup
    w("# Backup")
    w("BACKUP_RETENTION_DAILY=7")
    w("BACKUP_RETENTION_WEEKLY=4")
    w("BACKUP_CRON=0 3 * * *")
    w()

    return "\n".join(lines)


def generate_caddyfile(config):
    """Generate Caddyfile for reverse proxying all enabled apps.

    Per-service routing is defined in static Caddyfile snippets under
    services/*/Caddyfile. This function generates the minimal stub that
    loads the snippets and creates site blocks.
    """
    enabled = config["enabled_apps"]
    mode = config["mode"]
    domain = config.get("domain", "localhost")
    lines = []

    def w(line=""):
        lines.append(line)

    # Global options
    w("{")
    if mode == "local":
        w("\tauto_https off")
    else:
        w(f"\temail {config['acme_email']}")
    w("}")
    w()

    # Load all service Caddyfile snippets (including _base)
    w("import /etc/caddy/services/*/Caddyfile")
    w()

    def site_address(port=None, subdomain=None):
        if mode == "local":
            return f":{port}"
        return f"{subdomain}.{domain}" if subdomain else domain

    # --- Homepage ---
    w(f"{site_address(APP_PORTS['homepage'], APP_SUBDOMAINS['homepage'])} {{")
    w("\timport homepage")
    w("}")
    w()

    # --- Keycloak ---
    w(f"{site_address(APP_PORTS['keycloak'], APP_SUBDOMAINS['keycloak'])} {{")
    w("\timport keycloak")
    w("}")
    w()

    # --- RustFS Console (local only) ---
    if mode == "local":
        w(f":{APP_PORTS['rustfs_console']} {{")
        w("\timport rustfs-console")
        w("}")
        w()

    # --- App blocks (import snippets) ---
    for app_id, app in APP_REGISTRY.items():
        if app_id not in enabled:
            continue
        addr = site_address(app["port"], app["subdomain"])
        w(f"{addr} {{")
        w(f"\timport {app_id}")
        w("}")
        w()

    # --- LiveKit (prod only, needs TLS termination) ---
    if "meet" in enabled and mode == "prod":
        subdomain = APP_SUBDOMAINS["livekit"]
        w(f"{subdomain}.{domain} {{")
        w("\timport livekit")
        w("}")
        w()

    # --- S3 / RustFS (prod, public access for presigned URLs) ---
    if mode == "prod":
        subdomain = APP_SUBDOMAINS["rustfs"]
        w(f"{subdomain}.{domain} {{")
        w("\timport rustfs-s3")
        w("}")
        w()

    # --- Fallback for disabled apps (prod only) ---
    if mode == "prod":
        disabled_addrs = []
        for app_id in APP_REGISTRY:
            if app_id not in enabled:
                subdomain = APP_REGISTRY[app_id].get("subdomain")
                if subdomain:
                    disabled_addrs.append(f"{subdomain}.{domain}")
        if disabled_addrs:
            home_url = f"https://{APP_SUBDOMAINS['homepage']}.{domain}"
            html = (
                '<html><body style="font-family:system-ui,sans-serif;text-align:center;padding:4em">'
                '<h2>App not enabled</h2>'
                '<p>This application is not enabled on this MaSuite instance.</p>'
                f'<p><a href="{home_url}">Back to homepage</a></p>'
                '</body></html>'
            )
            w(f"# Disabled apps - fallback page")
            w(f"{', '.join(disabled_addrs)} {{")
            w(f'\theader Content-Type "text/html; charset=utf-8"')
            w(f"\trespond `{html}` 404")
            w("}")
            w()

    return "\n".join(lines)


def generate_livekit_config(env_values):
    """Generate livekit.yaml with actual secret values (not templates)."""
    api_key = env_values.get("LIVEKIT_API_KEY", "")
    api_secret = env_values.get("LIVEKIT_API_SECRET", "")
    redis_password = env_values.get("REDIS_PASSWORD", "")
    lines = [
        "port: 7880",
        "rtc:",
        "  tcp_port: 7881",
        "  udp_port: 7882",
        "  use_external_ip: true",
        "redis:",
        "  address: redis:6379",
        f"  password: {redis_password}",
        "  db: 6",
        "keys:",
        f"  {api_key}: {api_secret}",
        "logging:",
        "  level: info",
        "",
    ]
    return "\n".join(lines)


def generate_homepage_config(config):
    """Generate config.json for the homepage."""
    enabled = config["enabled_apps"]
    mode = config["mode"]
    domain = config.get("domain", "localhost")

    apps = []
    for app_id, app in APP_REGISTRY.items():
        if app_id not in enabled:
            continue
        if mode == "local":
            url = f"http://localhost:{app['port']}"
        else:
            url = f"https://{app['subdomain']}.{domain}"
        apps.append({
            "id": app_id,
            "name": app["label"],
            "description": app["description"],
            "url": url,
        })

    return json.dumps({"apps": apps}, indent=2)


def generate_gaufre_services(config):
    """Generate gaufre-services.json for the La Gaufre v2 widget."""
    enabled = config["enabled_apps"]
    mode = config["mode"]
    domain = config.get("domain", "localhost")

    services = []
    for i, (app_id, app) in enumerate(APP_REGISTRY.items(), 1):
        if app_id not in enabled:
            continue
        if mode == "local":
            url = f"http://localhost:{app['port']}"
        else:
            url = f"https://{app['subdomain']}.{domain}"
        svc = {"id": i, "name": app["label"], "url": url}
        if app.get("logo"):
            svc["logo"] = app["logo"]
        services.append(svc)

    return json.dumps({"services": services}, indent=2)


def generate_docs_theme(config):
    """Generate Docs theme customization JSON with Gaufre waffle config."""
    mode = config["mode"]
    domain = config.get("domain", "localhost")
    if mode == "local":
        api_url = f"http://localhost:{APP_PORTS['homepage']}/gaufre-services.json"
    else:
        api_url = f"https://{APP_SUBDOMAINS['homepage']}.{domain}/gaufre-services.json"
    return json.dumps({
        "waffle": {
            "apiUrl": api_url,
            "widgetPath": GAUFRE_SCRIPT_URL + "lagaufre.js",
        }
    }, indent=2)


def run(root_dir, preset_apps=None, preset_mode=None):
    """Run the interactive setup wizard."""
    print()
    print("  MaSuite - Self-hosted La Suite Numerique")
    print("  =========================================")
    print()

    # Check for existing .env
    env_path = os.path.join(root_dir, ".env")
    if os.path.exists(env_path):
        if not ask_yn("  Existing configuration found. Overwrite?", default=False):
            print("  Setup cancelled.")
            return

    # -- Step 1: App selection --
    if preset_apps:
        enabled = set(a.strip() for a in preset_apps.split(","))
        enabled = enabled & set(APP_REGISTRY.keys())
        print(f"  Apps: {', '.join(sorted(enabled))}")
    else:
        print("  Which apps do you want to install?")
        print()
        for i, (key, app) in enumerate(APP_REGISTRY.items(), 1):
            default_mark = "*" if app["default_enabled"] else " "
            print(f"    {i}. [{default_mark}] {app['label']:15s} {app['description']}")
        print()
        default_str = ",".join(
            str(i) for i, (key, app) in enumerate(APP_REGISTRY.items(), 1)
            if app["default_enabled"]
        )
        raw = ask("  Enter numbers separated by commas", default_str)
        enabled = set()
        app_ids = list(APP_REGISTRY.keys())
        for part in raw.split(","):
            part = part.strip()
            try:
                idx = int(part)
                if 1 <= idx <= len(app_ids):
                    enabled.add(app_ids[idx - 1])
            except (ValueError, TypeError):
                continue

    if not enabled:
        print("  No apps selected. Aborting.")
        return

    config = {"enabled_apps": enabled, "root_dir": root_dir}

    # -- Step 2: Mode --
    print()
    if preset_mode:
        mode = preset_mode
        print(f"  Mode: {mode}")
    else:
        print("  Where will you run MaSuite?")
        print()
        print("    1. Production server  -- custom domain, HTTPS (Let's Encrypt)")
        print("    2. Local machine      -- localhost, HTTP, works offline")
        print()
        choice = ask("  Choose", "1")
        mode = "local" if choice == "2" else "prod"

    config["mode"] = mode

    # -- Step 3: Domain & email (prod only) --
    if mode == "prod":
        print()
        config["domain"] = ask("  Domain name (e.g. suite.example.com)")
        if not config["domain"]:
            print("  Domain is required for production mode. Aborting.")
            return
        config["acme_email"] = ask(
            "  Email for Let's Encrypt certificates",
            f"admin@{config['domain']}",
        )
    else:
        config["domain"] = "localhost"

    # -- Step 4: App-specific options --

    # Drive: editor choice
    if "drive" in enabled:
        print()
        print("  Drive: which document editor?")
        print()
        print("    1. Collabora Online  -- recommended, open source")
        print("    2. OnlyOffice        -- alternative office suite")
        print()
        choice = ask("  Choose", "1")
        config["drive_editor"] = "onlyoffice" if choice == "2" else "collabora"

    # Conversations: LLM endpoint (optional)
    if "conversations" in enabled:
        print()
        print("  Conversations needs an LLM endpoint (OpenAI-compatible API).")
        print("  OpenRouter (https://openrouter.ai) gives access to many models.")
        print("  You can configure this later in .env if you skip it now.")
        print()
        config["llm_backend"] = ask(
            "  LLM API base URL", "https://openrouter.ai/api/v1"
        )
        if config["llm_backend"]:
            config["llm_api_key"] = ask("  LLM API key", "")
            config["llm_model"] = ask(
                "  Model name", "anthropic/claude-sonnet-4" if "openrouter" in config["llm_backend"] else ""
            )
        else:
            config["llm_api_key"] = ""
            config["llm_model"] = ""

    # Messages: SMTP relay (optional)
    if "messages" in enabled:
        print()
        print("  Messages: email delivery.")
        print("  Most VPS providers block port 25. Use an SMTP relay (Mailgun, SES, ...)")
        print("  or leave empty for direct delivery. You can configure this later in .env.")
        print()
        if mode == "prod":
            config["mail_domain"] = ask("  Mail domain", config["domain"])
        else:
            config["mail_domain"] = "localhost"
        config["smtp_relay_host"] = ask("  SMTP relay host (leave empty to skip)", "")
        if config["smtp_relay_host"]:
            config["smtp_relay_user"] = ask("  SMTP relay username", "")
            config["smtp_relay_password"] = ask("  SMTP relay password", "")
        else:
            config["smtp_relay_user"] = ""
            config["smtp_relay_password"] = ""

    # -- Generate everything --
    print()
    print("  Generating configuration...", end=" ", flush=True)
    existing = _load_existing_env(root_dir)
    config["keycloak_admin_password"] = existing.get(
        "KEYCLOAK_ADMIN_PASSWORD", generate_password()
    )
    env_content = build_env(config)

    # Parse the generated env for values needed by other generators
    env_values = {}
    for line in env_content.splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env_values[k.strip()] = v.strip()

    caddyfile_content = generate_caddyfile(config)
    homepage_config_json = generate_homepage_config(config)
    gaufre_services_json = generate_gaufre_services(config)
    docs_theme_json = generate_docs_theme(config) if "docs" in enabled else None
    livekit_yaml = generate_livekit_config(env_values) if "meet" in enabled else None
    print("done")

    # Write files
    print("  Writing files...", end=" ", flush=True)

    with open(env_path, "w") as f:
        f.write(env_content)
    os.chmod(env_path, 0o600)

    caddy_dir = os.path.join(root_dir, "config", "caddy")
    os.makedirs(caddy_dir, exist_ok=True)
    with open(os.path.join(caddy_dir, "Caddyfile"), "w") as f:
        f.write(caddyfile_content)

    hp_dir = os.path.join(root_dir, "config", "homepage")
    os.makedirs(hp_dir, exist_ok=True)
    with open(os.path.join(hp_dir, "config.json"), "w") as f:
        f.write(homepage_config_json)
    with open(os.path.join(hp_dir, "gaufre-services.json"), "w") as f:
        f.write(gaufre_services_json)

    if docs_theme_json:
        with open(os.path.join(root_dir, "config", "docs-theme.json"), "w") as f:
            f.write(docs_theme_json)

    if livekit_yaml:
        lk_dir = os.path.join(root_dir, "config", "livekit")
        os.makedirs(lk_dir, exist_ok=True)
        with open(os.path.join(lk_dir, "livekit.yaml"), "w") as f:
            f.write(livekit_yaml)

    print("done")

    # -- Summary --
    print()
    print("  Configuration saved!")
    print()
    if not existing.get("KEYCLOAK_ADMIN_PASSWORD"):
        print(f"  Keycloak admin: admin / {config['keycloak_admin_password']}")
    else:
        print(f"  Keycloak admin password: (preserved from existing config)")
    print()

    if mode == "local":
        print("  URLs:")
        print(f"    Homepage      http://localhost:{APP_PORTS['homepage']}")
        for app_id, app in APP_REGISTRY.items():
            if app_id in enabled:
                print(f"    {app['label']:13s}  http://localhost:{app['port']}")
        print(f"    Keycloak      http://localhost:{APP_PORTS['keycloak']}")
    else:
        print("  URLs:")
        print(f"    Homepage      https://{APP_SUBDOMAINS['homepage']}.{config['domain']}")
        for app_id, app in APP_REGISTRY.items():
            if app_id in enabled:
                print(f"    {app['label']:13s}  https://{app['subdomain']}.{config['domain']}")
        print(f"    Keycloak      https://{APP_SUBDOMAINS['keycloak']}.{config['domain']}")

    print()

    # -- Docker check & optional install --
    from . import docker_utils
    if not docker_utils.ensure_docker():
        print("  Setup complete. Install Docker, then run: ./masuite start")
        return

    # -- Offer to start --
    if mode == "prod":
        print(f"  Make sure DNS is configured: *.{config['domain']} -> this server's IP")
        print()

    if ask_yn("  Start MaSuite now?"):
        print()
        from . import __main__ as cli
        import argparse
        cli.cmd_start(argparse.Namespace())
    else:
        print()
        print("  Run ./masuite start whenever you're ready.")
    print()
