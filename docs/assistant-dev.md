# Assistant Dev Notes

## Components

- `assistant/assistantd.py`: Daemon listening on a Unix socket, executing allowlisted actions.
- `assistant/assistant_cli.py`: CLI client that sends JSON requests to `assistantd`.
- `assistant/assistant_gui.py`: Tkinter desktop UI for chat/actions/settings.
- `configs/assistant-policy.json`: Policy indicating which actions are allowed and privileged.
- `/etc/aifirst/aifirst-ai.json`: Runtime settings (AI profiles + `assistant_permissions`).

## JSON protocol

Request:

```json
{
  "action": "ai_query",
  "params": {
    "mode": "ask",
    "profile": "local-ollama",
    "prompt": "How do I update Fedora safely?"
  },
  "approve": false,
  "dry_run": true
}
```

Response:

```json
{
  "ok": true,
  "action": "ai_query",
  "command": ["aifirst-ai", "--profile", "local-ollama", "ask", "How do I update Fedora safely?"],
  "command_str": "aifirst-ai --profile local-ollama ask 'How do I update Fedora safely?'",
  "privileged": false,
  "dry_run": true,
  "returncode": 0,
  "stdout": "",
  "stderr": "",
  "timestamp": "2026-03-05T00:00:00+00:00"
}
```

## Initial action set

- `system_update_check`
- `list_upgrades`
- `disk_usage_summary`
- `network_summary`
- `ai_query` (non-privileged, calls `aifirst-ai`)
- `install_package` (privileged)
- `remove_package` (privileged)

## Permissions modes

- `read_only`: blocks all privileged actions (install/remove/write actions)
- `full_access`: allows privileged actions, but each still requires `approve=true`

## Security model in v0

- No arbitrary shell commands are accepted.
- Package names are strictly validated.
- AI query mode is allowlisted (`ask` or `summarize`) with prompt length limits.
- AI profiles are name-validated and passed as argv (not shell).
- Assistant permission mode is enforced from `assistant_permissions` in assistant settings JSON.
- Privileged actions require `approve=true`.
- Every request/response is logged as JSON lines audit records.
