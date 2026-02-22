#!/bin/bash
set -euo pipefail

# MaSuite installer
# Usage: curl -sSL masuite.fr/install.sh | bash -s -- [--apps docs,meet,drive] [--mode local|prod]

REPO_URL="https://github.com/sylvinus/masuite"
INSTALL_DIR="${MASUITE_DIR:-$HOME/masuite}"

echo ""
echo "  __  __        ____        _ _       "
echo " |  \/  | __ _ / ___| _   _(_) |_ ___ "
echo " | |\/| |/ _\` |\___ \| | | | | __/ _ \\"
echo " | |  | | (_| | ___) | |_| | | ||  __/"
echo " |_|  |_|\__,_||____/ \__,_|_|\__\___|"
echo ""
echo " Self-hosted La Suite Numerique"
echo ""

# Parse arguments
APPS=""
MODE=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --apps) APPS="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Check dependencies
echo "Checking dependencies..."
for cmd in docker git python3; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "  ERROR: $cmd is required but not installed."
    echo "  Install it and try again."
    exit 1
  fi
  echo "  $cmd: OK"
done

if ! docker compose version &>/dev/null; then
  echo "  ERROR: docker compose v2 is required."
  echo "  See https://docs.docker.com/compose/install/"
  exit 1
fi
echo "  docker compose: OK"
echo ""

# Download MaSuite
if [ -d "$INSTALL_DIR" ]; then
  echo "Updating existing installation in $INSTALL_DIR..."
  cd "$INSTALL_DIR"
  git pull --quiet
else
  echo "Installing MaSuite to $INSTALL_DIR..."
  git clone --quiet "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

# Build setup command
SETUP_ARGS=""
if [ -n "$APPS" ]; then
  SETUP_ARGS="$SETUP_ARGS --apps $APPS"
fi
if [ -n "$MODE" ]; then
  SETUP_ARGS="$SETUP_ARGS --mode $MODE"
fi

# Run setup
echo ""
echo "Starting setup wizard..."
echo ""
python3 -m cli setup $SETUP_ARGS

echo ""
echo "Installation complete!"
echo "Run 'cd $INSTALL_DIR && ./masuite start' to start your services."
echo ""
