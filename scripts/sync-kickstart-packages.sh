#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
KS_FILE="${ROOT_DIR}/kickstarts/ai-first-fedora.ks"

if [[ ! -f "${KS_FILE}" ]]; then
  echo "Kickstart file not found: ${KS_FILE}" >&2
  exit 1
fi

TMP_LIST="$(mktemp)"
TMP_OUT="$(mktemp)"

cleanup() {
  rm -f "${TMP_LIST}" "${TMP_OUT}"
}
trap cleanup EXIT

"${SCRIPT_DIR}/compose-package-list.sh" > "${TMP_LIST}"

awk -v list_file="${TMP_LIST}" '
  BEGIN {
    while ((getline line < list_file) > 0) {
      pkg[++n] = line
    }
    close(list_file)
  }
  /# BEGIN_MANAGED_PACKAGES/ {
    print $0
    print "# Synced from manifests via scripts/sync-kickstart-packages.sh"
    for (i = 1; i <= n; i++) print pkg[i]
    in_block = 1
    next
  }
  /# END_MANAGED_PACKAGES/ {
    in_block = 0
    print $0
    next
  }
  in_block == 0 { print $0 }
' "${KS_FILE}" > "${TMP_OUT}"

mv "${TMP_OUT}" "${KS_FILE}"
echo "Updated managed package block in ${KS_FILE}"
