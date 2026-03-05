#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ISO_PATH="${1:-$(find "${ROOT_DIR}/out/iso" -maxdepth 1 -name '*.iso' | head -n 1)}"
VM_DISK="${ROOT_DIR}/out/vm/aifirst-smoke.qcow2"

if [[ -z "${ISO_PATH}" || ! -f "${ISO_PATH}" ]]; then
  echo "ISO not found. Pass path as first argument or build one in out/iso." >&2
  exit 1
fi

if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
  echo "Missing required command: qemu-system-x86_64" >&2
  exit 1
fi

mkdir -p "$(dirname "${VM_DISK}")"
if [[ ! -f "${VM_DISK}" ]]; then
  qemu-img create -f qcow2 "${VM_DISK}" 40G >/dev/null
fi

qemu-system-x86_64 \
  -enable-kvm \
  -m 4096 \
  -smp 4 \
  -boot d \
  -cdrom "${ISO_PATH}" \
  -drive file="${VM_DISK}",if=virtio,format=qcow2 \
  -net nic -net user \
  -display default
