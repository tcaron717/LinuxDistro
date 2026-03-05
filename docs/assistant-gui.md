# Assistant GUI

## Overview

`assistant-gui` provides a desktop interface for users who do not want to use CLI.

It supports:

- Chat with AI (`ai_query`) using selected profile and mode
- System actions (disk, network, update checks)
- Package install/remove with confirmation dialogs
- Profile management (add/update/remove/set default)
- Permission mode management (`read_only` / `full_access`)

## Launch

- From app menu: `AI First Assistant`
- From terminal: `assistant-gui`

## Runtime dependencies

- `assistantd` running and reachable via socket (`/run/assistantd.sock` by default)
- `python3-tkinter` installed

## Settings source

By default the GUI reads/writes:

- `~/.config/aifirst/aifirst-ai.json`

You can point it to system settings in the GUI top bar:

- `/etc/aifirst/aifirst-ai.json`

## Notes

- Privileged actions require both:
  - permission mode set to `full_access`
  - explicit approval in backend action flow
- If socket path is different in development, set it in the GUI top bar.
