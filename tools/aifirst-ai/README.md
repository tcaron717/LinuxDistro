# aifirst-ai

`aifirst-ai` is a lightweight CLI tool for your AI-first Fedora spin.

## Features

- Provider abstraction:
  - `ollama` (local, private-by-default)
  - `openai_compatible` (any OpenAI-compatible API endpoint)
- Commands:
  - `ask`: General prompt
  - `summarize`: Summarize stdin or a file
  - `doctor`: Validate config and provider connectivity
- Config file support at `/etc/aifirst/aifirst-ai.json` or `~/.config/aifirst/aifirst-ai.json`

## Quick start

```bash
aifirst-ai ask "How do I check disk usage on Fedora?"
echo "Long text..." | aifirst-ai summarize
aifirst-ai --profile openai-prod ask "Summarize dnf history usage."
```
