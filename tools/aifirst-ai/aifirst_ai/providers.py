from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .config import AppConfig


@dataclass
class AIResponse:
    text: str
    provider: str
    model: str


class ProviderError(Exception):
    pass


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout_sec: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Connection failed: {exc}") from exc


def chat(cfg: AppConfig, user_prompt: str, system_prompt: str | None = None) -> AIResponse:
    system = system_prompt or cfg.system_prompt
    if cfg.provider == "ollama":
        return _chat_ollama(cfg, user_prompt, system)
    if cfg.provider == "openai_compatible":
        return _chat_openai_compatible(cfg, user_prompt, system)
    raise ProviderError(f"Unsupported provider: {cfg.provider}")


def doctor(cfg: AppConfig) -> str:
    if cfg.provider == "ollama":
        url = f"{cfg.ollama_base_url.rstrip('/')}/api/tags"
        req = urllib.request.Request(url=url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout_sec) as resp:
                _ = resp.read()
            return f"ok: ollama reachable at {cfg.ollama_base_url}"
        except Exception as exc:
            raise ProviderError(f"ollama check failed: {exc}") from exc
    if cfg.provider == "openai_compatible":
        if not cfg.openai_api_key:
            raise ProviderError("missing openai_api_key")
        return "ok: openai_compatible config looks valid (key present)"
    raise ProviderError(f"unsupported provider: {cfg.provider}")


def _chat_ollama(cfg: AppConfig, user_prompt: str, system_prompt: str) -> AIResponse:
    url = f"{cfg.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    data = _post_json(url, payload, {"Content-Type": "application/json"}, cfg.timeout_sec)
    try:
        text = str(data["message"]["content"]).strip()
    except Exception as exc:
        raise ProviderError(f"Malformed ollama response: {data}") from exc
    return AIResponse(text=text, provider="ollama", model=cfg.model)


def _chat_openai_compatible(cfg: AppConfig, user_prompt: str, system_prompt: str) -> AIResponse:
    if not cfg.openai_api_key:
        raise ProviderError("Missing API key for openai_compatible provider")
    url = f"{cfg.openai_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg.openai_api_key}",
    }
    data = _post_json(url, payload, headers, cfg.timeout_sec)
    try:
        text = str(data["choices"][0]["message"]["content"]).strip()
    except Exception as exc:
        raise ProviderError(f"Malformed openai-compatible response: {data}") from exc
    return AIResponse(text=text, provider="openai_compatible", model=cfg.model)
