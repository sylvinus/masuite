"""Post-start Keycloak configuration: set client secret and redirect URIs.

Standard Keycloak does not resolve ${env.*} placeholders in realm imports,
so we set the client secret via the Admin REST API after startup.

The realm JSON (config/keycloak/masuite-realm.json) is a static file that
defines all scopes, protocol mappers, and client attributes. This module
only handles the two dynamic parts: the client secret and the redirect URIs
(which depend on the deployment mode and domain).
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request


def _load_env(root_dir):
    """Load .env file as a dict."""
    import os
    env = {}
    env_path = os.path.join(root_dir, ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def _get_admin_token(kc_url, admin_user, admin_password):
    """Get an admin access token from Keycloak."""
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": admin_user,
        "password": admin_password,
    }).encode()
    req = urllib.request.Request(
        f"{kc_url}/realms/master/protocol/openid-connect/token",
        data=data,
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def _api(kc_url, path, token, method="GET", data=None):
    """Keycloak Admin API request."""
    url = f"{kc_url}/admin/realms/masuite{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"Keycloak API {e.code}: {error_body}") from e


def _wait_for_keycloak(kc_url, timeout=120):
    """Wait for Keycloak to be ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{kc_url}/realms/master")
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            time.sleep(2)
    return False


def _get_keycloak_internal_url(root_dir):
    """Get a URL to reach Keycloak from the host.

    In prod mode, the external URL (https://auth.domain) may not work yet
    (certs not issued), so we find the container IP and connect directly.
    """
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
    return None


def configure(root_dir):
    """Set the Keycloak OIDC client secret and redirect URIs after startup."""
    env = _load_env(root_dir)
    admin_user = env.get("KEYCLOAK_ADMIN_USER", "admin")
    admin_password = env.get("KEYCLOAK_ADMIN_PASSWORD", "")

    # Try internal Docker URL first, fall back to external
    kc_url = _get_keycloak_internal_url(root_dir)
    if not kc_url:
        kc_url = env.get("KEYCLOAK_URL", "http://localhost:9200")

    if not admin_password:
        return

    secret = env.get("SHARED_OIDC_CLIENT_SECRET", "")
    if not secret:
        return

    # Compute redirect URIs based on deployment mode
    mode = env.get("MASUITE_MODE", "local")
    domain = env.get("BASE_DOMAIN", "")
    if mode == "prod" and domain:
        redirect_uris = [f"https://*.{domain}/*"]
        web_origins = [f"https://*.{domain}"]
        post_logout = f"https://*.{domain}/*"
    else:
        redirect_uris = ["*"]
        web_origins = ["*"]
        post_logout = "+"

    print("Configuring Keycloak...", end=" ", flush=True)

    # Wait for Keycloak
    if not _wait_for_keycloak(kc_url):
        print("FAILED (Keycloak not ready)")
        return

    try:
        token = _get_admin_token(kc_url, admin_user, admin_password)
    except Exception:
        # Keycloak may still be importing realm, retry
        time.sleep(5)
        try:
            token = _get_admin_token(kc_url, admin_user, admin_password)
        except Exception as e:
            print(f"FAILED ({e})")
            return

    # Find the masuite client
    clients = _api(kc_url, "/clients", token)
    client = next((c for c in clients if c["clientId"] == "masuite"), None)

    if not client:
        # Client should exist from realm import, but create if missing
        try:
            _api(kc_url, "/clients", token, method="POST", data={
                "clientId": "masuite",
                "name": "MaSuite",
                "enabled": True,
                "protocol": "openid-connect",
                "publicClient": False,
                "clientAuthenticatorType": "client-secret",
                "secret": secret,
                "standardFlowEnabled": True,
                "directAccessGrantsEnabled": False,
                "serviceAccountsEnabled": True,
                "redirectUris": redirect_uris,
                "webOrigins": web_origins,
                "attributes": {
                    "post.logout.redirect.uris": post_logout,
                    "user.info.response.signature.alg": "RS256",
                },
            })
            print("done (created client)")
            return
        except RuntimeError as e:
            print(f"FAILED (could not create client: {e})")
            return

    # Update client: secret + redirect URIs
    needs_update = False

    if client.get("secret") != secret:
        client["secret"] = secret
        needs_update = True

    if client.get("redirectUris") != redirect_uris:
        client["redirectUris"] = redirect_uris
        needs_update = True

    if client.get("webOrigins") != web_origins:
        client["webOrigins"] = web_origins
        needs_update = True

    attrs = client.get("attributes", {})
    if attrs.get("post.logout.redirect.uris") != post_logout:
        attrs["post.logout.redirect.uris"] = post_logout
        client["attributes"] = attrs
        needs_update = True

    if needs_update:
        try:
            _api(kc_url, f"/clients/{client['id']}", token, method="PUT", data=client)
        except RuntimeError:
            pass  # Best effort

    print("done")
