#!/usr/bin/env python3
import argparse
import json
import re
import socket
import sys
from pathlib import Path
from typing import Any

PROFILE_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
DEFAULT_SETTINGS_PATH = Path.home() / ".config" / "aifirst" / "aifirst-ai.json"


def parse_action_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI-first assistant CLI")
    parser.add_argument("action", help="Action name to execute")
    parser.add_argument("--package", help="Package name (required for install_package/remove_package)")
    parser.add_argument("--prompt", help="Prompt text (used for ai_query action)")
    parser.add_argument("--mode", choices=["ask", "summarize"], help="AI mode for ai_query action")
    parser.add_argument("--profile", help="AI profile name for ai_query action")
    parser.add_argument("--approve", action="store_true", help="Required for privileged actions")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved command without executing it")
    parser.add_argument("--socket-path", default="/run/assistantd.sock", help="assistantd Unix socket path")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args(argv)


def parse_settings_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="assistant-cli settings manager")
    path_parent = argparse.ArgumentParser(add_help=False)
    path_parent.add_argument(
        "--settings-path",
        default=str(DEFAULT_SETTINGS_PATH),
        help="Path to aifirst-ai profile config JSON",
    )
    sub = parser.add_subparsers(dest="settings_cmd", required=True)
    sub.add_parser("list", help="List configured AI API profiles", parents=[path_parent])

    add = sub.add_parser("add", help="Add or update an AI API profile", parents=[path_parent])
    add.add_argument("--name", required=True, help="Profile name")
    add.add_argument("--provider", choices=["ollama", "openai_compatible"], required=True)
    add.add_argument("--model", required=True, help="Model name")
    add.add_argument("--base-url", help="Provider base URL")
    add.add_argument("--api-key", default="", help="API key (optional)")
    add.add_argument("--api-key-env", default="", help="Environment variable name containing API key")
    add.add_argument("--set-default", action="store_true", help="Set this profile as default")

    rem = sub.add_parser("remove", help="Remove an AI API profile", parents=[path_parent])
    rem.add_argument("--name", required=True, help="Profile name")

    default = sub.add_parser("set-default", help="Set default profile", parents=[path_parent])
    default.add_argument("--name", required=True, help="Profile name")

    set_perm = sub.add_parser("set-permissions", help="Set assistant permission mode", parents=[path_parent])
    set_perm.add_argument("--mode", choices=["read_only", "full_access"], required=True)

    sub.add_parser("get-permissions", help="Show assistant permission mode", parents=[path_parent])

    show = sub.add_parser("show", help="Show full config JSON", parents=[path_parent])
    show.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    init = sub.add_parser("init", help="Create default config if missing", parents=[path_parent])
    init.add_argument("--force", action="store_true", help="Overwrite existing config")
    return parser.parse_args(argv)


def _validate_profile_name(name: str) -> None:
    if not PROFILE_RE.match(name):
        raise ValueError("Invalid profile name")


def _default_settings() -> dict[str, Any]:
    return {
        "assistant_permissions": "read_only",
        "default_profile": "local-ollama",
        "profiles": {
            "local-ollama": {
                "provider": "ollama",
                "model": "llama3.2",
                "ollama_base_url": "http://127.0.0.1:11434",
            }
        },
        "timeout_sec": 60,
        "system_prompt": (
            "You are a Linux assistant for an AI-first Fedora distribution. "
            "Prioritize safe, reproducible commands and explain briefly."
        ),
    }


def _load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _default_settings()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Invalid settings JSON")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        data["profiles"] = {}
    if str(data.get("assistant_permissions", "")).strip() not in {"read_only", "full_access"}:
        data["assistant_permissions"] = "read_only"
    return data


def _save_settings(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def _profile_from_args(args: argparse.Namespace) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "provider": args.provider,
        "model": args.model,
    }
    if args.provider == "ollama":
        profile["ollama_base_url"] = args.base_url or "http://127.0.0.1:11434"
    if args.provider == "openai_compatible":
        profile["openai_base_url"] = args.base_url or "https://api.openai.com/v1"
        if args.api_key:
            profile["openai_api_key"] = args.api_key
        if args.api_key_env:
            profile["openai_api_key_env"] = args.api_key_env
    return profile


def handle_settings(argv: list[str]) -> int:
    args = parse_settings_args(argv)
    settings_path = Path(args.settings_path)
    if args.settings_cmd == "init":
        if settings_path.exists() and not args.force:
            print(f"settings exists: {settings_path}")
            return 0
        data = _default_settings()
        _save_settings(settings_path, data)
        print(f"initialized settings at {settings_path}")
        return 0

    data = _load_settings(settings_path)
    profiles = data.setdefault("profiles", {})

    if args.settings_cmd == "list":
        default_profile = str(data.get("default_profile", "")).strip()
        if not profiles:
            print("No profiles configured.")
            return 0
        for name in sorted(profiles.keys()):
            marker = "*" if name == default_profile else " "
            provider = profiles[name].get("provider", "unknown")
            model = profiles[name].get("model", "unknown")
            print(f"{marker} {name} ({provider}, model={model})")
        return 0

    if args.settings_cmd == "add":
        _validate_profile_name(args.name)
        profiles[args.name] = _profile_from_args(args)
        if args.set_default or not data.get("default_profile"):
            data["default_profile"] = args.name
        _save_settings(settings_path, data)
        print(f"saved profile '{args.name}' to {settings_path}")
        return 0

    if args.settings_cmd == "remove":
        _validate_profile_name(args.name)
        if args.name not in profiles:
            print(f"profile not found: {args.name}", file=sys.stderr)
            return 1
        del profiles[args.name]
        if data.get("default_profile") == args.name:
            data["default_profile"] = next(iter(sorted(profiles.keys())), "")
        _save_settings(settings_path, data)
        print(f"removed profile '{args.name}'")
        return 0

    if args.settings_cmd == "set-default":
        _validate_profile_name(args.name)
        if args.name not in profiles:
            print(f"profile not found: {args.name}", file=sys.stderr)
            return 1
        data["default_profile"] = args.name
        _save_settings(settings_path, data)
        print(f"default profile set to '{args.name}'")
        return 0

    if args.settings_cmd == "set-permissions":
        data["assistant_permissions"] = args.mode
        _save_settings(settings_path, data)
        print(f"assistant permissions set to '{args.mode}'")
        return 0

    if args.settings_cmd == "get-permissions":
        print(str(data.get("assistant_permissions", "read_only")).strip() or "read_only")
        return 0

    if args.settings_cmd == "show":
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print(f"settings path: {settings_path}")
            print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    print("Unknown settings command", file=sys.stderr)
    return 2


def send_request(socket_path: str, payload: dict[str, Any]) -> dict[str, Any]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(socket_path)
        sock.sendall(json.dumps(payload).encode("utf-8"))
        chunks: list[bytes] = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
    raw = b"".join(chunks)
    if not raw:
        raise RuntimeError("No response from assistantd")
    return json.loads(raw.decode("utf-8"))


def handle_action(argv: list[str]) -> int:
    args = parse_action_args(argv)
    params: dict[str, Any] = {}
    if args.package:
        params["package"] = args.package
    if args.prompt:
        params["prompt"] = args.prompt
    if args.mode:
        params["mode"] = args.mode
    if args.profile:
        params["profile"] = args.profile

    payload = {
        "action": args.action,
        "params": params,
        "approve": args.approve,
        "dry_run": args.dry_run,
    }

    try:
        response = send_request(args.socket_path, payload)
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(response, indent=2, sort_keys=True))
    else:
        if response.get("ok"):
            print(f"ok: {response.get('action')}")
            print(f"command: {response.get('command_str')}")
            if response.get("permission_mode"):
                print(f"permission-mode: {response.get('permission_mode')}")
            if response.get("dry_run"):
                print("dry-run: true")
            rc = response.get("returncode")
            if rc is not None:
                print(f"returncode: {rc}")
            out = str(response.get("stdout", "")).strip()
            err = str(response.get("stderr", "")).strip()
            if out:
                print("--- stdout ---")
                print(out)
            if err:
                print("--- stderr ---")
                print(err)
        else:
            print(f"error: {response.get('error', 'unknown error')}", file=sys.stderr)
            return 1

    return 0 if response.get("ok") else 1


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "settings":
        return handle_settings(argv[1:])
    return handle_action(argv)


if __name__ == "__main__":
    raise SystemExit(main())
