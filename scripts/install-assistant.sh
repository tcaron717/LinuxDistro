#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

BIN_DIR="${BIN_DIR:-/usr/local/bin}"
ETC_DIR="${ETC_DIR:-/etc/aifirst}"
UNIT_DIR="${UNIT_DIR:-/etc/systemd/system}"
APP_DIR="${APP_DIR:-/usr/share/applications}"

install -d "${BIN_DIR}" "${ETC_DIR}" "${UNIT_DIR}" "${APP_DIR}"
install -m 0755 "${ROOT_DIR}/assistant/assistantd.py" "${BIN_DIR}/assistantd"
install -m 0755 "${ROOT_DIR}/assistant/assistant_cli.py" "${BIN_DIR}/assistant-cli"
install -m 0755 "${ROOT_DIR}/assistant/assistant_gui.py" "${BIN_DIR}/assistant-gui"
install -m 0644 "${ROOT_DIR}/configs/assistant-policy.json" "${ETC_DIR}/assistant-policy.json"
if [[ -f "${ROOT_DIR}/configs/aifirst-ai.json" ]]; then
  install -m 0644 "${ROOT_DIR}/configs/aifirst-ai.json" "${ETC_DIR}/aifirst-ai.json"
fi
install -m 0644 "${ROOT_DIR}/systemd/assistantd.service" "${UNIT_DIR}/assistantd.service"
install -m 0644 "${ROOT_DIR}/desktop/assistant-gui.desktop" "${APP_DIR}/assistant-gui.desktop"

if command -v systemctl >/dev/null 2>&1; then
  systemctl daemon-reload || true
  systemctl enable assistantd.service || true
fi

echo "Installed assistantd, assistant-cli, and assistant-gui."
