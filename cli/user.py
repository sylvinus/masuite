"""User management via Keycloak Admin REST API (pure stdlib)."""

import json
import os
import secrets
import string
import urllib.error
import urllib.parse
import urllib.request


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


def _get_admin_token(keycloak_url, admin_user, admin_password):
    """Get an admin access token from Keycloak."""
    token_url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": admin_user,
        "password": admin_password,
    }).encode()

    req = urllib.request.Request(token_url, data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read())
        return body["access_token"]


def _api_request(keycloak_url, path, token, method="GET", data=None):
    """Make an authenticated request to the Keycloak Admin API."""
    url = f"{keycloak_url}/admin/realms/masuite{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (201, 204):
                return None
            body = resp.read()
            if not body:
                return None
            return json.loads(body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"Keycloak API error {e.code}: {error_body}") from e


def _generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_keycloak_url(root_dir, env):
    """Get a working Keycloak URL, preferring internal Docker IP."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f",
             "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
             "masuite-keycloak-1"],
            capture_output=True, text=True, timeout=5,
        )
        ip = result.stdout.strip()
        if result.returncode == 0 and ip:
            return f"http://{ip}:8080"
    except Exception:
        pass
    return env.get("KEYCLOAK_URL", "http://localhost:9200")


def create(root_dir, email, password=None):
    """Create a user in Keycloak."""
    env = _load_env(root_dir)
    keycloak_url = _get_keycloak_url(root_dir, env)
    admin_user = env.get("KEYCLOAK_ADMIN_USER", "admin")
    admin_password = env.get("KEYCLOAK_ADMIN_PASSWORD")

    if not admin_password:
        print("Error: KEYCLOAK_ADMIN_PASSWORD must be set in .env")
        return

    if not password:
        password = _generate_password()
        show_password = True
    else:
        show_password = False

    print(f"Creating user {email}...", end=" ", flush=True)

    token = _get_admin_token(keycloak_url, admin_user, admin_password)

    user_data = {
        "email": email,
        "username": email,
        "enabled": True,
        "emailVerified": True,
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False,
            }
        ],
    }

    try:
        _api_request(keycloak_url, "/users", token, method="POST", data=user_data)
        print("done")
        if show_password:
            print(f"  Email:    {email}")
            print(f"  Password: {password}")
    except RuntimeError as e:
        if "409" in str(e):
            print(f"FAILED: user {email} already exists")
        else:
            print(f"FAILED: {e}")


def list_users(root_dir):
    """List all users in the masuite realm."""
    env = _load_env(root_dir)
    keycloak_url = _get_keycloak_url(root_dir, env)
    admin_user = env.get("KEYCLOAK_ADMIN_USER", "admin")
    admin_password = env.get("KEYCLOAK_ADMIN_PASSWORD")

    if not admin_password:
        print("Error: KEYCLOAK_ADMIN_PASSWORD must be set in .env")
        return

    token = _get_admin_token(keycloak_url, admin_user, admin_password)
    users = _api_request(keycloak_url, "/users?max=100", token)

    if not users:
        print("No users found.")
        return

    print(f"{'Email':40s} {'Enabled':8s} {'Created'}")
    print("-" * 70)
    for u in users:
        email = u.get("email", u.get("username", "?"))
        enabled = "yes" if u.get("enabled") else "no"
        created = str(u.get("createdTimestamp", ""))[:10]
        print(f"{email:40s} {enabled:8s} {created}")
