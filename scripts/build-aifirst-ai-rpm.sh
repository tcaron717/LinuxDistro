#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TOOL_DIR="${ROOT_DIR}/tools/aifirst-ai"
SPEC_FILE="${ROOT_DIR}/packaging/rpm/aifirst-ai.spec"

if ! command -v rpmbuild >/dev/null 2>&1; then
  echo "Missing rpmbuild. Install rpm-build." >&2
  exit 1
fi

VERSION="$(python3 -c 'import tomllib;print(tomllib.load(open("tools/aifirst-ai/pyproject.toml","rb"))["project"]["version"])')"
NAME="aifirst-ai"
TARBALL="${NAME}-${VERSION}.tar.gz"

TOPDIR="${ROOT_DIR}/out/rpmbuild"
mkdir -p "${TOPDIR}"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

STAGE="${ROOT_DIR}/out/${NAME}-${VERSION}"
rm -rf "${STAGE}"
mkdir -p "${STAGE}"
cp -R "${TOOL_DIR}"/* "${STAGE}/"
mkdir -p "${STAGE}/configs"
cp "${ROOT_DIR}/configs/aifirst-ai.json" "${STAGE}/configs/aifirst-ai.json"

tar -C "${ROOT_DIR}/out" -czf "${TOPDIR}/SOURCES/${TARBALL}" "${NAME}-${VERSION}"
cp "${SPEC_FILE}" "${TOPDIR}/SPECS/${NAME}.spec"

rpmbuild -ba "${TOPDIR}/SPECS/${NAME}.spec" --define "_topdir ${TOPDIR}"
echo "RPM build complete: ${TOPDIR}/RPMS"
