#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

BASE_MANIFEST="${ROOT_DIR}/manifests/base-packages.txt"
AI_MANIFEST="${ROOT_DIR}/manifests/ai-packages.txt"

if [[ ! -f "${BASE_MANIFEST}" || ! -f "${AI_MANIFEST}" ]]; then
  echo "Missing package manifests." >&2
  exit 1
fi

cat "${BASE_MANIFEST}" "${AI_MANIFEST}" \
  | sed 's/[[:space:]]*$//' \
  | sed '/^[[:space:]]*$/d' \
  | sed '/^[[:space:]]*#/d' \
  | sort -u
