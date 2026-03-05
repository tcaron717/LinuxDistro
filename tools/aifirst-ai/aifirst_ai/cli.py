from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .providers import ProviderError, chat, doctor


def _read_text_from_args_or_stdin(text_arg: str | None, file_arg: str | None) -> str:
    if text_arg:
        return text_arg
    if file_arg:
        return Path(file_arg).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aifirst-ai", description="AI tool for AI-first Fedora")
    parser.add_argument(
        "--profile",
        help="Config profile name from aifirst-ai.json profiles map",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ask = sub.add_parser("ask", help="Send a general prompt")
    ask.add_argument("prompt", nargs="?", help="Prompt text")
    ask.add_argument("--file", help="Read prompt from file")
    ask.add_argument("--system", help="Override system prompt")

    summ = sub.add_parser("summarize", help="Summarize input text")
    summ.add_argument("text", nargs="?", help="Text to summarize")
    summ.add_argument("--file", help="Read text from file")
    summ.add_argument("--system", help="Override system prompt")

    sub.add_parser("doctor", help="Check provider configuration/connectivity")
    return parser


def do_ask(args: argparse.Namespace) -> int:
    cfg = load_config(args.profile)
    prompt = _read_text_from_args_or_stdin(args.prompt, args.file).strip()
    if not prompt:
        print("No prompt provided. Pass text, --file, or pipe stdin.", file=sys.stderr)
        return 2
    try:
        resp = chat(cfg, prompt, args.system)
    except ProviderError as exc:
        print(f"provider error: {exc}", file=sys.stderr)
        return 1
    print(resp.text)
    return 0


def do_summarize(args: argparse.Namespace) -> int:
    cfg = load_config(args.profile)
    text = _read_text_from_args_or_stdin(args.text, args.file).strip()
    if not text:
        print("No text provided. Pass text, --file, or pipe stdin.", file=sys.stderr)
        return 2
    prompt = (
        "Summarize the following text in concise bullet points with practical Linux-user context:\n\n"
        f"{text}"
    )
    try:
        resp = chat(cfg, prompt, args.system)
    except ProviderError as exc:
        print(f"provider error: {exc}", file=sys.stderr)
        return 1
    print(resp.text)
    return 0


def do_doctor(args: argparse.Namespace) -> int:
    cfg = load_config(args.profile)
    try:
        msg = doctor(cfg)
    except ProviderError as exc:
        print(f"doctor failed: {exc}", file=sys.stderr)
        return 1
    print(msg)
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "ask":
        return do_ask(args)
    if args.command == "summarize":
        return do_summarize(args)
    if args.command == "doctor":
        return do_doctor(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
