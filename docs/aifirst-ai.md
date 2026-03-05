# aifirst-ai Tool

## Purpose

`aifirst-ai` is a distro-native CLI for AI interactions with local-first defaults.

## Commands

- `aifirst-ai ask "<prompt>"`
- `aifirst-ai summarize "<text>"`
- `echo "<text>" | aifirst-ai summarize`
- `aifirst-ai doctor`
- `aifirst-ai --profile openai-prod ask "<prompt>"`

## Configuration

Default config path:

- `/etc/aifirst/aifirst-ai.json`

User config path:

- `~/.config/aifirst/aifirst-ai.json`

Profile-oriented schema:

```json
{
  "assistant_permissions": "read_only",
  "default_profile": "local-ollama",
  "profiles": {
    "local-ollama": {
      "provider": "ollama",
      "model": "llama3.2",
      "ollama_base_url": "http://127.0.0.1:11434"
    },
    "openai-prod": {
      "provider": "openai_compatible",
      "model": "gpt-4o-mini",
      "openai_base_url": "https://api.openai.com/v1",
      "openai_api_key_env": "OPENAI_API_KEY"
    }
  }
}
```

Assistant permissions values:

- `read_only`: assistant can read/analyze and answer prompts, but cannot execute privileged mutation actions.
- `full_access`: assistant can execute privileged mutation actions when explicitly approved in CLI requests.

Environment overrides:

- `AIFIRST_AI_PROVIDER` (`ollama` or `openai_compatible`)
- `AIFIRST_AI_MODEL`
- `AIFIRST_AI_OLLAMA_URL`
- `AIFIRST_AI_OPENAI_URL`
- `AIFIRST_AI_OPENAI_API_KEY`
- `AIFIRST_AI_TIMEOUT_SEC`

## Packaging flow

1. `make build-aifirst-ai-rpm`
2. Copy RPM(s) from `out/rpmbuild/RPMS/` to your repo dir (for example `out/repo/`)
3. `make create-repo REPO=out/repo`
4. Ensure `kickstarts/ai-first-fedora.ks` has your local repo configured
5. `make build-iso`
