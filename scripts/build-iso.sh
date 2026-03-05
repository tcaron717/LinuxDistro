#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
KS_FILE="${ROOT_DIR}/kickstarts/ai-first-fedora.ks"
OUT_DIR="${ROOT_DIR}/out/iso"
CACHE_DIR="${ROOT_DIR}/out/cache"
RELEASEVER="${RELEASEVER:-40}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd livemedia-creator
need_cmd qemu-img

mkdir -p "${OUT_DIR}" "${CACHE_DIR}"

echo "Building ISO from ${KS_FILE}"
echo "Output dir: ${OUT_DIR}"

sudo livemedia-creator \
  --make-iso \
  --ks "${KS_FILE}" \
  --project "AIFirstFedora" \
  --releasever "${RELEASEVER}" \
  --volid "AIFEDORA-${RELEASEVER}" \
  --resultdir "${OUT_DIR}" \
  --cache "${CACHE_DIR}" \
  --image-name "aifirst-fedora-${RELEASEVER}.qcow2"

echo "ISO build complete. Check ${OUT_DIR}"
