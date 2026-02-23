# Submit Bot Codex VSCode

Safe auto-submit automation for **VS Code Codex workflows** and **selected web forms**.

- Desktop mode: Python + Windows UI Automation (UIA-first).
- Browser mode: Chrome/Edge Manifest V3 extension.
- Safety model: allowlist-only, dry-run support, cooldowns, visible active indicators.

## Why this project

Most auto-click tools are risky by default. This project is built to be constrained and auditable:

1. No unknown apps or websites are clicked.
2. You must explicitly allow process/title or URL patterns.
3. You can run dry-run mode before enabling live clicks.
4. You can pause instantly (`Ctrl+Alt+P` desktop, popup toggle extension).

## Project Structure

```text
desktop/   -> Windows desktop bot (Python 3.11+ recommended)
extension/ -> Chrome/Edge MV3 extension
scripts/   -> setup, release, growth/launch automation scripts
docs/      -> SEO pack, store listing copy, privacy policy, monetization notes
replit/    -> traffic landing page template for Replit
```

## Quick Start

### Desktop (Windows)

```powershell
.\setup.ps1
cd desktop
.venv\Scripts\Activate.ps1
python main.py
```

VS Code Codex button profile:

```powershell
python main.py --config .\config.vscode_codex.toml
```

Live click profile:

```powershell
python main.py --config .\config.vscode_codex.live.toml
```

### Extension (Chrome/Edge)

1. Open `chrome://extensions` or `edge://extensions`
2. Enable Developer mode
3. Click **Load unpacked**
4. Select `extension/`
5. Configure allowlist in Options before enabling

## Focus Behavior (Important)

If a target app steals focus when the click is invoked, the desktop bot now supports best-effort foreground restore:

- `preserve_focus = true`
- `focus_restore_delay_ms = 40`

This reduces focus jumps, but some applications can still force activation based on their own UI behavior.

## Publish + Growth Toolkit

Build release artifacts:

```powershell
.\scripts\build_release.ps1
```

Generate professional launch copy pack (GitHub/LinkedIn/X/Reddit/Dev.to/Product Hunt/HN/Replit):

```powershell
python .\scripts\generate_launch_kit.py --config .\marketing\launch_config.json --output .\marketing\out
```

All-in-one growth helper:

```powershell
.\scripts\launch_growth.ps1
```

Optional GitHub About/Topics updater (requires `gh auth login`):

```powershell
.\scripts\apply_github_metadata.ps1 -DryRun
.\scripts\apply_github_metadata.ps1
```

Generated files include:

- GitHub description + topics
- Platform-specific post drafts
- Launch checklist
- Chrome Web Store short description draft

## Store + SEO Docs

- GitHub SEO pack: `docs/seo/github_seo_pack.md`
- Demo recording script: `docs/seo/demo_recording_script.md`
- Chrome/Edge listing draft: `docs/store/chrome_web_store_listing.md`
- Privacy policy template: `docs/privacy/privacy-policy.md`
- Public privacy page for store submission: `privacy.html`
- Monetization playbook: `docs/seo/monetization_playbook.md`

## Replit Traffic Page

`replit/` contains a lightweight landing page you can deploy to Replit to route traffic to your repo/releases.

Note: desktop runtime is Windows-specific and should run on Windows, not in Replit.

## Security Disclaimer

Automation can execute real actions. You are responsible for your allowlists and live mode settings. Validate in dry-run mode first.
