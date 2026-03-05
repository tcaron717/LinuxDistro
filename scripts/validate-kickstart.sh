#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
KS_FILE="${ROOT_DIR}/kickstarts/ai-first-fedora.ks"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    return 1
  fi
}

need_cmd ksvalidator

if [[ ! -f "${KS_FILE}" ]]; then
  echo "Kickstart file not found: ${KS_FILE}" >&2
  exit 1
fi

ksvalidator "${KS_FILE}"
echo "Kickstart validation passed: ${KS_FILE}"
