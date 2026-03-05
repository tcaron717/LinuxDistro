# Assistant Architecture (Starter)

## Goal

Provide an AI-integrated Linux experience where users can ask for system tasks in plain language with explicit permission boundaries.

## Suggested components

1. `assistantd` (system service)
- Exposes local API (Unix socket)
- Handles intent routing and policy checks
- Executes safe automation handlers

2. `assistant-cli`
- Terminal entry point for power users
- Supports dry-run and explain modes

3. `assistant-ui`
- Desktop panel app for chat + task confirmations
- Shows action plans before privileged changes

4. Provider adapters
- Local model runtime adapter (for offline/private use)
- Cloud API adapter (for stronger models)

## Safety model (minimum)

- All privileged actions require explicit user confirmation
- Commands are allowlisted by capability, not free-form shell
- Every action generates an audit log with timestamp and outcome

## First capabilities to implement

- System update check and apply
- Install/remove package by name
- Network diagnostics summary
- Disk space cleanup suggestions
- Driver status and recommendations
