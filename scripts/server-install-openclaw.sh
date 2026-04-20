#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="${OPENCLAW_RUNTIME_ROOT:-/data/openclaw-runtime}"
OPENCLAW_HOME_DIR="${OPENCLAW_RUNTIME_HOME:-$INSTALL_ROOT/home}"
BIN_DIR="$INSTALL_ROOT/bin"

echo "OpenClaw clean runtime installer"
echo "Install root: $INSTALL_ROOT"
echo "Runtime home: $OPENCLAW_HOME_DIR"
echo
echo "This script creates a new runtime. It does not delete existing OpenClaw data."
echo

sudo mkdir -p "$INSTALL_ROOT" "$OPENCLAW_HOME_DIR"
sudo chown -R "$(id -un):$(id -gn)" "$INSTALL_ROOT"
chmod 700 "$OPENCLAW_HOME_DIR"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required. Install it with: sudo apt install -y curl"
  exit 1
fi

echo "Downloading and installing OpenClaw CLI..."
curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install-cli.sh \
  | bash -s -- --prefix "$INSTALL_ROOT" --no-onboard

if [ -x "$BIN_DIR/openclaw" ]; then
  CLI="$BIN_DIR/openclaw"
elif command -v openclaw >/dev/null 2>&1; then
  CLI="$(command -v openclaw)"
elif command -v openclaw-cn >/dev/null 2>&1; then
  CLI="$(command -v openclaw-cn)"
else
  echo "OpenClaw CLI was not found after install."
  echo "Check the installer output above."
  exit 1
fi

echo
echo "Installed CLI:"
"$CLI" --version || true

cat <<EOF

Next commands:

  export PATH="$BIN_DIR:\$PATH"
  export OPENCLAW_HOME="$OPENCLAW_HOME_DIR"
  "$CLI" onboard --install-daemon
  "$CLI" security audit --fix
  "$CLI" security audit
  "$CLI" status

If the CLI command is openclaw-cn instead of openclaw, replace "$CLI" with openclaw-cn.

Keep the gateway local-only until the security audit is clean.
EOF

