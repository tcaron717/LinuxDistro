from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SYSTEM_PROMPT = (
    "You are a Linux assistant for an AI-first Fedora distribution. "
    "Prioritize safe, reproducible commands and explain briefly."
)


@dataclass
class AppConfig:
    profile_name: str = "default"
    provider: str = "ollama"
    model: str = "llama3.2"
    ollama_base_url: str = "http://127.0.0.1:11434"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_api_key_env: str = ""
    timeout_sec: int = 60
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


def _candidate_paths() -> list[Path]:
    etc = Path("/etc/aifirst/aifirst-ai.json")
    user = Path.home() / ".config" / "aifirst" / "aifirst-ai.json"
    return [etc, user]


def _load_raw_config() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for p in _candidate_paths():
        if p.exists():
            try:
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
    return data


def _resolve_profile(data: dict[str, Any], requested_profile: str | None) -> tuple[str, dict[str, Any]]:
    profiles = data.get("profiles", {})
    if isinstance(profiles, dict) and profiles:
        profile_name = requested_profile or str(data.get("default_profile", "")).strip() or next(iter(profiles.keys()))
        profile_data = profiles.get(profile_name)
        if isinstance(profile_data, dict):
            return profile_name, profile_data
    # Backward compatibility with single-provider schema.
    return requested_profile or "default", data


def load_config(profile: str | None = None) -> AppConfig:
    data = _load_raw_config()
    profile_name, resolved = _resolve_profile(data, profile)

    cfg = AppConfig(
        profile_name=profile_name,
        provider=str(resolved.get("provider", data.get("provider", "ollama"))),
        model=str(resolved.get("model", data.get("model", "llama3.2"))),
        ollama_base_url=str(resolved.get("ollama_base_url", data.get("ollama_base_url", "http://127.0.0.1:11434"))),
        openai_base_url=str(resolved.get("openai_base_url", data.get("openai_base_url", "https://api.openai.com/v1"))),
        openai_api_key=str(resolved.get("openai_api_key", data.get("openai_api_key", ""))),
        openai_api_key_env=str(resolved.get("openai_api_key_env", data.get("openai_api_key_env", ""))),
        timeout_sec=int(resolved.get("timeout_sec", data.get("timeout_sec", 60))),
        system_prompt=str(resolved.get("system_prompt", data.get("system_prompt", DEFAULT_SYSTEM_PROMPT))),
    )

    cfg.provider = os.getenv("AIFIRST_AI_PROVIDER", cfg.provider)
    cfg.model = os.getenv("AIFIRST_AI_MODEL", cfg.model)
    cfg.ollama_base_url = os.getenv("AIFIRST_AI_OLLAMA_URL", cfg.ollama_base_url)
    cfg.openai_base_url = os.getenv("AIFIRST_AI_OPENAI_URL", cfg.openai_base_url)
    key_from_env_var_name = cfg.openai_api_key_env.strip()
    key_from_named_env = os.getenv(key_from_env_var_name, "") if key_from_env_var_name else ""
    cfg.openai_api_key = os.getenv("AIFIRST_AI_OPENAI_API_KEY", key_from_named_env or cfg.openai_api_key)
    cfg.timeout_sec = int(os.getenv("AIFIRST_AI_TIMEOUT_SEC", str(cfg.timeout_sec)))
    return cfg
