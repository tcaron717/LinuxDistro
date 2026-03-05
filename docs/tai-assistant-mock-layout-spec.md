# tAI Assistant Mock Screenshot Layout Spec

## Purpose

Provide a clear visual blueprint for screenshots and future UI polish while keeping native system theme/colors.

## Theme

- Inherit system theme and colors (GTK/Tk defaults).
- No custom color palette required.
- Keep contrast and spacing readable on both light and dark system themes.

## Window

- App name: `tAI Assistant`
- Default size: `940 x 680`
- Layout model: top global bar + tabbed content area

## Global Layout Wireframe

```text
+--------------------------------------------------------------------------------------+
| tAI Assistant                                                                        |
|--------------------------------------------------------------------------------------|
| Socket Path [ /run/assistantd.sock                  ] Settings Path [ ~/.config/... ]|
| [Reload Settings]                                                                    |
|--------------------------------------------------------------------------------------|
| [ Chat ] [ System Actions ] [ Settings ]                                             |
|======================================================================================|
| (Selected tab content area)                                                          |
|                                                                                      |
|                                                                                      |
+--------------------------------------------------------------------------------------+
```

## Chat Tab Mock

```text
+--------------------------------------------------------------------------------------+
| Mode [ask v]   Profile [local-ollama v____________________]   [Send]                |
|--------------------------------------------------------------------------------------|
| Prompt                                                                               |
| +----------------------------------------------------------------------------------+ |
| | How do I check GPU info?                                                         | |
| |                                                                                  | |
| +----------------------------------------------------------------------------------+ |
| Response                                                                             |
| +----------------------------------------------------------------------------------+ |
| | Use `lspci | grep -i vga` ...                                                    | |
| |                                                                                  | |
| +----------------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------------+
```

## System Actions Tab Mock

```text
+--------------------------------------------------------------------------------------+
| [Disk Usage] [Network Summary] [List Upgrades] [Check Updates]                      |
|--------------------------------------------------------------------------------------|
| Package [ htop________________________ ] [Install] [Remove]                         |
|--------------------------------------------------------------------------------------|
| Output                                                                               |
| +----------------------------------------------------------------------------------+ |
| | $ dnf list --upgrades                                                            | |
| | ...                                                                              | |
| +----------------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------------+
```

## Settings Tab Mock

```text
+--------------------------------------------------------------------------------------+
| Profiles                    | Name      [openai-prod____________________]            |
| +-------------------------+ | Provider  [openai_compatible v___________]            |
| | * local-ollama (...)    | | Model     [gpt-4o-mini____________________]          |
| |   openai-prod (...)     | | Base URL  [https://api.openai.com/v1_____]          |
| |                         | | API Key Env[OPENAI_API_KEY_______________]           |
| +-------------------------+ | [Add/Update Profile] [Save Settings]                 |
| [Set Default] [Delete]      |                                                       |
|                              | Assistant Permissions                                 |
|                              | (o) Read Only    ( ) Full Access                     |
|                              | Read Only blocks privileged actions...                |
+--------------------------------------------------------------------------------------+
```

## Screenshot Capture Checklist

- Ensure window title reads `tAI Assistant`.
- Capture one screenshot per tab.
- Use realistic sample outputs in text areas.
- Show one profile selected and one default-marked profile in Settings.
- Show permission mode state clearly (`Read Only` or `Full Access`).
