#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
KS_FILE="${ROOT_DIR}/kickstarts/ai-first-fedora.ks"
LOCAL_REPO="${ROOT_DIR}/out/repo"
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

ANACONDA_PID_FILE="/run/user/0/anaconda.pid"
if [[ -e "${ANACONDA_PID_FILE}" ]]; then
  ANACONDA_PID="$(sudo cat "${ANACONDA_PID_FILE}" 2>/dev/null || true)"
  if [[ "${ANACONDA_PID}" =~ ^[0-9]+$ ]] && [[ -r "/proc/${ANACONDA_PID}/cmdline" ]] && tr '\0' ' ' < "/proc/${ANACONDA_PID}/cmdline" | grep -q anaconda; then
    echo "Anaconda is already running with PID ${ANACONDA_PID}; stop it before rebuilding." >&2
    exit 1
  fi
  sudo rm -f "${ANACONDA_PID_FILE}"
fi

if [[ -e "${OUT_DIR}" ]]; then
  echo "Output path already exists: ${OUT_DIR}" >&2
  echo "Move or remove it before rebuilding so livemedia-creator can create a fresh result directory." >&2
  exit 1
fi

if [[ ! -f "${LOCAL_REPO}/repodata/repomd.xml" ]] || ! compgen -G "${LOCAL_REPO}/aifirst-ai-*.rpm" >/dev/null; then
  echo "Missing local aifirst-ai RPM repository: ${LOCAL_REPO}" >&2
  echo "Run 'make build-aifirst-ai-rpm', copy the RPM into out/repo/, and run 'make create-repo REPO=out/repo'." >&2
  exit 1
fi

mkdir -p "$(dirname "${OUT_DIR}")"

BUILD_KS="$(mktemp "${TMPDIR:-/tmp}/aifirst-fedora.XXXXXX.ks")"
trap 'rm -f "${BUILD_KS}"' EXIT

awk -v repo_path="${LOCAL_REPO}" '
  /# LOCAL_AIFIRST_REPO/ {
    print "repo --name=ai-first-local --baseurl=file://" repo_path
    next
  }
  { print }
' "${KS_FILE}" > "${BUILD_KS}"

echo "Building Fedora ${RELEASEVER} ${ARCH} ISO from ${KS_FILE}"
echo "Output dir: ${OUT_DIR}"

sudo livemedia-creator \
  --make-iso \
  --no-virt \
  --ks "${BUILD_KS}" \
  --project "AIFirstFedora-${ARCH}" \
  --releasever "${RELEASEVER}" \
  --volid "AIFEDORA-${RELEASEVER}-${ARCH}" \
  --resultdir "${OUT_DIR}" \
  --image-name "aifirst-fedora-${RELEASEVER}-${ARCH}.qcow2"

echo "ISO build complete. Check ${OUT_DIR}"
