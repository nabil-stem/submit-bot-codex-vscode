# Desktop Mode (Windows 11)

Python 3.11+ background app that watches allowlisted windows for allowlisted button text and clicks safely.

## Features

- UI Automation first (`pywinauto`, backend `uia`).
- Optional image fallback only when enabled.
- Strict allowlist by process name and window title substring.
- Dry-run mode.
- Global pause/resume hotkey.
- System tray controls and visible runtime state.
- Rotating logs.
- Unit tests with mocked provider layer.

## Install

```powershell
cd desktop
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

Custom config path:

```powershell
python main.py --config C:\path\to\config.toml
```

VS Code Codex strict profile:

```powershell
python main.py --config .\config.vscode_codex.toml
```

This profile targets the Codex panel `Submit` button label variants that include return icons (`Submit ⏎`, `Submit ↩`, `Submit ↵`) to avoid matching unrelated "submit" text elsewhere in VS Code.

Live-click variant:

```powershell
python main.py --config .\config.vscode_codex.live.toml
```

## Config

On first run, config is created at:

`%APPDATA%\SubmitAutoClicker\config.toml`

Key settings:

- `allowed_processes`
- `allowed_window_title_contains`
- `button_texts`
- `poll_interval_ms`
- `click_cooldown_ms`
- `require_button_enabled`
- `require_near_text_contains`
- `allow_focus`
- `preserve_focus`
- `focus_restore_delay_ms`
- `dry_run`
- `enable_image_fallback`
- `image_fallback_confidence`
- `image_button_templates`

## Tray Controls

- Pause/Resume
- Dry-run toggle
- Reload config
- Open config file location
- Open logs
- Quit

## Hotkey

Default pause/resume hotkey:

`ctrl+alt+p`

Change via `hotkey_pause_resume` in config and reload from tray menu.

## Tests

```powershell
pytest -q
```

## Build EXE (Optional)

```powershell
pip install pyinstaller
pyinstaller submit_autoclicker.spec
```

Output:

`desktop\dist\submit_autoclicker\submit_autoclicker.exe`

## Limitations

- Some app surfaces are not fully exposed through UIA.
- Minimized windows can be inaccessible to UIA or image search.
- Image fallback requires visible content and can only click with `allow_focus=true`.
- Global hotkeys may be blocked by endpoint/security policy on managed devices.
- Some apps can still pull focus after invoke. `preserve_focus=true` restores the previous foreground window on a best-effort basis.

## Troubleshooting

1. Check `%APPDATA%\SubmitAutoClicker\logs\submit_autoclicker.log`.
2. Confirm target process name and exact window title snippet are in allowlist.
3. Start with `dry_run=true` and verify match logs before enabling live mode.
4. If no candidates are found, inspect whether the button is a UIA `Button` control type.
5. If needed, enable image fallback and provide template images.

## Security Disclaimer

Automation can trigger irreversible actions. Keep allowlists narrow, keep dry-run on until verified, and review logs regularly.

