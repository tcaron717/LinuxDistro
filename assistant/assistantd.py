#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PACKAGE_RE = re.compile(r"^[a-zA-Z0-9._+-]+$")
AI_MODE_RE = re.compile(r"^(ask|summarize)$")
PROFILE_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
MAX_PROMPT_CHARS = 8000
PERMISSION_MODES = {"read_only", "full_access"}


class AssistantError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_policy(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "actions" not in data or not isinstance(data["actions"], dict):
        raise AssistantError("Invalid policy: missing actions object")
    return data


def load_permission_mode(config_path: Path) -> str:
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        mode = str(data.get("assistant_permissions", "read_only")).strip()
    except Exception:
        mode = "read_only"
    if mode not in PERMISSION_MODES:
        return "read_only"
    return mode


def render_command(action: str, params: dict[str, Any]) -> list[str]:
    if action == "system_update_check":
        return ["dnf", "check-update"]
    if action == "list_upgrades":
        return ["dnf", "list", "--upgrades"]
    if action == "disk_usage_summary":
        return ["df", "-h"]
    if action == "network_summary":
        return ["nmcli", "general", "status"]
    if action in ("install_package", "remove_package"):
        package = str(params.get("package", "")).strip()
        if not PACKAGE_RE.match(package):
            raise AssistantError("Invalid package name")
        if action == "install_package":
            return ["dnf", "install", "-y", package]
        return ["dnf", "remove", "-y", package]
    if action == "ai_query":
        mode = str(params.get("mode", "ask")).strip()
        prompt = str(params.get("prompt", "")).strip()
        profile = str(params.get("profile", "")).strip()
        if not AI_MODE_RE.match(mode):
            raise AssistantError("Invalid ai_query mode (allowed: ask, summarize)")
        if not prompt:
            raise AssistantError("ai_query requires a non-empty prompt")
        if len(prompt) > MAX_PROMPT_CHARS:
            raise AssistantError(f"ai_query prompt exceeds {MAX_PROMPT_CHARS} characters")
        if profile and not PROFILE_RE.match(profile):
            raise AssistantError("Invalid ai_query profile")
        cmd = ["aifirst-ai"]
        if profile:
            cmd.extend(["--profile", profile])
        cmd.extend([mode, prompt])
        return cmd
    raise AssistantError(f"Unknown action: {action}")


def run_action(
    policy: dict[str, Any],
    action: str,
    params: dict[str, Any],
    approve: bool,
    dry_run: bool,
    timeout_sec: int,
    permission_mode: str,
) -> dict[str, Any]:
    action_cfg = policy["actions"].get(action)
    if not action_cfg:
        raise AssistantError("Action is not allowed by policy")

    privileged = bool(action_cfg.get("privileged", False))
    if permission_mode == "read_only" and privileged:
        raise AssistantError("Permission mode read_only blocks privileged actions")
    if privileged and not approve:
        raise AssistantError("Privileged action requires approve=true")

    cmd = render_command(action, params)
    result: dict[str, Any] = {
        "action": action,
        "command": cmd,
        "command_str": shlex.join(cmd),
        "privileged": privileged,
        "permission_mode": permission_mode,
        "timestamp": utc_now(),
        "dry_run": dry_run,
    }
    if dry_run:
        result["ok"] = True
        result["stdout"] = ""
        result["stderr"] = ""
        result["returncode"] = 0
        return result

    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    result["ok"] = proc.returncode == 0
    result["stdout"] = proc.stdout
    result["stderr"] = proc.stderr
    result["returncode"] = proc.returncode
    return result


def write_audit(log_path: Path, payload: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")


def handle_client(
    conn: socket.socket,
    policy: dict[str, Any],
    assistant_config_path: Path,
    log_path: Path,
    timeout_sec: int,
) -> None:
    with conn:
        raw = conn.recv(1024 * 1024)
        if not raw:
            return
        try:
            request = json.loads(raw.decode("utf-8"))
            action = str(request.get("action", "")).strip()
            params = request.get("params", {}) or {}
            approve = bool(request.get("approve", False))
            dry_run = bool(request.get("dry_run", False))
            permission_mode = load_permission_mode(assistant_config_path)
            response = run_action(
                policy,
                action,
                params,
                approve,
                dry_run,
                timeout_sec,
                permission_mode,
            )
        except Exception as exc:  # pylint: disable=broad-except
            response = {
                "ok": False,
                "error": str(exc),
                "timestamp": utc_now(),
            }
        write_audit(log_path, {"request": request if "request" in locals() else {}, "response": response})
        conn.sendall(json.dumps(response).encode("utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI-first distro assistant daemon")
    parser.add_argument(
        "--socket-path",
        default="/run/assistantd.sock",
        help="Unix domain socket path",
    )
    parser.add_argument(
        "--policy-path",
        default="/etc/aifirst/assistant-policy.json",
        help="Policy JSON path",
    )
    parser.add_argument(
        "--audit-log",
        default="/var/log/aifirst/assistantd.log",
        help="Audit log path",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=120,
        help="Per-command timeout in seconds",
    )
    parser.add_argument(
        "--assistant-config-path",
        default="/etc/aifirst/aifirst-ai.json",
        help="Assistant settings JSON path (includes assistant_permissions)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    socket_path = Path(args.socket_path)
    policy_path = Path(args.policy_path)
    assistant_config_path = Path(args.assistant_config_path)
    log_path = Path(args.audit_log)

    try:
        policy = read_policy(policy_path)
    except Exception as exc:
        print(f"Failed loading policy: {exc}", file=sys.stderr)
        return 1

    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(socket_path))
        os.chmod(socket_path, 0o660)
        server.listen(16)
        print(f"assistantd listening on {socket_path}")
        while True:
            conn, _addr = server.accept()
            t = threading.Thread(
                target=handle_client,
                args=(conn, policy, assistant_config_path, log_path, args.timeout_sec),
                daemon=True,
            )
            t.start()


if __name__ == "__main__":
    raise SystemExit(main())
