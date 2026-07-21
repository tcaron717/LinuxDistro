#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
KS_FILE="${ROOT_DIR}/kickstarts/ai-first-fedora.ks"
RELEASEVER="${RELEASEVER:-44}"
ARCH="${ARCH:-$(uname -m)}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This ISO build requires a Fedora Linux build host." >&2
  exit 1
fi

normalize_arch() {
  case "$1" in
    x86_64) echo "x86_64" ;;
    aarch64|arm64) echo "aarch64" ;;
    *)
      echo "Unsupported architecture: $1. Supported architectures: x86_64, aarch64" >&2
      exit 1
      ;;
  esac
}

ARCH="$(normalize_arch "${ARCH}")"
HOST_ARCH="$(normalize_arch "$(uname -m)")"

if [[ "${ARCH}" != "${HOST_ARCH}" ]]; then
  echo "ARCH=${ARCH} requires a matching Fedora build host (detected ${HOST_ARCH})." >&2
  exit 1
fi

OUT_DIR="${ROOT_DIR}/out/iso/${ARCH}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd livemedia-creator
need_cmd qemu-img

if [[ -e "${OUT_DIR}" ]]; then
  echo "Output path already exists: ${OUT_DIR}" >&2
  echo "Move or remove it before rebuilding so livemedia-creator can create a fresh result directory." >&2
  exit 1
fi

mkdir -p "$(dirname "${OUT_DIR}")"

echo "Building Fedora ${RELEASEVER} ${ARCH} ISO from ${KS_FILE}"
echo "Output dir: ${OUT_DIR}"

sudo livemedia-creator \
  --make-iso \
  --no-virt \
  --ks "${KS_FILE}" \
  --project "AIFirstFedora-${ARCH}" \
  --releasever "${RELEASEVER}" \
  --volid "AIFEDORA-${RELEASEVER}-${ARCH}" \
  --resultdir "${OUT_DIR}" \
  --image-name "aifirst-fedora-${RELEASEVER}-${ARCH}.qcow2"

echo "ISO build complete. Check ${OUT_DIR}"
