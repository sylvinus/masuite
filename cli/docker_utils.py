"""Docker detection and auto-installation."""

import os
import shutil
import subprocess
import sys


def is_docker_available():
    """Check if docker and docker compose v2 are available."""
    if not shutil.which("docker"):
        return False
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True, check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def detect_distro():
    """Detect Linux distribution. Returns (id, pretty_name) or (None, None)."""
    try:
        with open("/etc/os-release") as f:
            info = {}
            for line in f:
                if "=" in line:
                    key, _, val = line.strip().partition("=")
                    info[key] = val.strip('"')
            return info.get("ID"), info.get("PRETTY_NAME", info.get("ID", "Linux"))
    except FileNotFoundError:
        return None, None


def _run(cmd, **kwargs):
    """Run a command, print it if verbose."""
    return subprocess.run(cmd, **kwargs)


def install_docker():
    """Install Docker via the official get.docker.com script. Returns True on success."""
    distro_id, distro_name = detect_distro()

    if distro_id not in ("debian", "ubuntu"):
        print(f"  Automatic Docker install is only supported on Debian and Ubuntu.")
        if distro_id:
            print(f"  Detected: {distro_name}")
        print(f"  Install Docker manually: https://docs.docker.com/engine/install/")
        return False

    print(f"  Detected {distro_name}")

    # Determine how to get root
    is_root = os.geteuid() == 0
    has_sudo = shutil.which("sudo") is not None

    if not is_root and not has_sudo:
        print("  Root or sudo access is required to install Docker.")
        print("  Re-run as root: su -c './masuite setup'")
        return False

    sudo = [] if is_root else ["sudo"]

    # Ensure we have curl or wget (install curl if neither available)
    if not shutil.which("curl") and not shutil.which("wget"):
        print("  Installing curl...")
        r = _run([*sudo, "apt-get", "update", "-qq"], check=False)
        if r.returncode != 0:
            print("  Failed to run apt-get update.")
            return False
        r = _run([*sudo, "apt-get", "install", "-y", "-qq", "curl"], check=False)
        if r.returncode != 0:
            print("  Failed to install curl.")
            return False

    # Pick download tool
    if shutil.which("curl"):
        download = ["curl", "-fsSL", "https://get.docker.com"]
    else:
        download = ["wget", "-qO-", "https://get.docker.com"]

    print("  Installing Docker via get.docker.com...")
    print()

    # Download and pipe to sh
    try:
        dl = subprocess.Popen(download, stdout=subprocess.PIPE)
        result = _run([*sudo, "sh"], stdin=dl.stdout, check=False)
        dl.wait()
        if result.returncode != 0:
            print()
            print("  Docker installation failed.")
            return False
    except Exception as e:
        print(f"  Docker installation failed: {e}")
        return False

    # Add current user to docker group if not root
    if not is_root:
        user = os.environ.get("USER", "")
        if user:
            _run([*sudo, "usermod", "-aG", "docker", user], check=False)
            print()
            print(f"  Added {user} to the docker group.")

            if not _test_docker_access():
                print(f"  Please log out and back in for Docker permissions to take effect,")
                print(f"  then run: ./masuite start")
                return False

    print()
    print("  Docker installed successfully!")
    return True


def _test_docker_access():
    """Test if current user can run docker."""
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True, check=True, timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def ensure_docker():
    """Check for Docker and offer to install it. Returns True if Docker is available."""
    if is_docker_available():
        return True

    has_docker_bin = shutil.which("docker") is not None

    if has_docker_bin:
        print("  Docker is installed but docker compose v2 is not available.")
        print("  Update Docker or install the compose plugin:")
        print("  https://docs.docker.com/compose/install/")
        return False

    print("  Docker is not installed.")
    print()

    try:
        answer = input("  Install Docker now? [Y/n]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    if answer and not answer.lower().startswith("y"):
        print()
        print("  Install Docker manually: https://docs.docker.com/engine/install/")
        return False

    print()
    return install_docker()


def require_docker():
    """Ensure Docker is available or exit."""
    if is_docker_available():
        return
    print()
    print("  Docker is required for this command.")
    if not ensure_docker():
        sys.exit(1)
