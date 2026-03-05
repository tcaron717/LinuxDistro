#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <repo_dir>" >&2
  exit 1
fi

REPO_DIR="$1"

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Repo directory does not exist: ${REPO_DIR}" >&2
  exit 1
fi

if ! command -v createrepo_c >/dev/null 2>&1; then
  echo "Missing required command: createrepo_c" >&2
  exit 1
fi

RPM_COUNT="$(find "${REPO_DIR}" -maxdepth 1 -name '*.rpm' | wc -l | tr -d ' ')"
if [[ "${RPM_COUNT}" -eq 0 ]]; then
  echo "No RPMs found in ${REPO_DIR}" >&2
  exit 1
fi

createrepo_c --update "${REPO_DIR}"
echo "Local RPM repo metadata created in ${REPO_DIR}"
