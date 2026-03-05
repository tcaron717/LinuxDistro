#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

python3 - <<'PY'
import json
from pathlib import Path

from assistant.assistantd import read_policy, run_action

root = Path(".").resolve()
policy = read_policy(root / "configs" / "assistant-policy.json")

# Non-privileged action should pass without approve.
resp = run_action(
    policy,
    "disk_usage_summary",
    {},
    approve=False,
    dry_run=True,
    timeout_sec=10,
    permission_mode="read_only",
)
assert resp["ok"] is True
assert "df -h" in resp["command_str"]

# ai_query should map to aifirst-ai safely.
resp = run_action(
    policy,
    "ai_query",
    {"mode": "ask", "prompt": "How do I update Fedora safely?", "profile": "local-ollama"},
    approve=False,
    dry_run=True,
    timeout_sec=10,
    permission_mode="read_only",
)
assert resp["ok"] is True
assert "aifirst-ai --profile local-ollama ask" in resp["command_str"]
assert "--profile local-ollama" in resp["command_str"]

# ai_query should reject invalid modes.
try:
    run_action(
        policy,
        "ai_query",
        {"mode": "shell", "prompt": "x"},
        approve=False,
        dry_run=True,
        timeout_sec=10,
        permission_mode="read_only",
    )
except Exception as exc:
    assert "Invalid ai_query mode" in str(exc)
else:
    raise AssertionError("Expected ai_query with invalid mode to fail")

# ai_query should reject invalid profile names.
try:
    run_action(
        policy,
        "ai_query",
        {"mode": "ask", "prompt": "x", "profile": "bad profile"},
        approve=False,
        dry_run=True,
        timeout_sec=10,
        permission_mode="read_only",
    )
except Exception as exc:
    assert "Invalid ai_query profile" in str(exc)
else:
    raise AssertionError("Expected ai_query with invalid profile to fail")

# Privileged action in read_only mode should fail.
try:
    run_action(
        policy,
        "install_package",
        {"package": "htop"},
        approve=True,
        dry_run=True,
        timeout_sec=10,
        permission_mode="read_only",
    )
except Exception as exc:
    assert "read_only blocks privileged actions" in str(exc)
else:
    raise AssertionError("Expected privileged action to fail in read_only mode")

# Privileged action in full_access without approve should fail.
try:
    run_action(
        policy,
        "install_package",
        {"package": "htop"},
        approve=False,
        dry_run=True,
        timeout_sec=10,
        permission_mode="full_access",
    )
except Exception as exc:
    assert "approve=true" in str(exc)
else:
    raise AssertionError("Expected privileged action to fail without approve")

# Privileged action with approve in full_access should pass.
resp = run_action(
    policy,
    "install_package",
    {"package": "htop"},
    approve=True,
    dry_run=True,
    timeout_sec=10,
    permission_mode="full_access",
)
assert resp["ok"] is True
assert "dnf install -y htop" in resp["command_str"]
assert resp["permission_mode"] == "full_access"

print("assistant core tests passed")
PY
