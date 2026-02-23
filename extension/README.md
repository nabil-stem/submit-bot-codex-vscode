# Browser Extension Mode (Chrome/Edge MV3)

Allowlist-gated submit auto-clicker for web pages.

## Safety Defaults

- Global automation is OFF by default.
- Dry-run mode is ON by default.
- URL allowlist is empty by default.
- Per-site toggle can disable any site even if allowlisted.

## Features

- MutationObserver-driven DOM monitoring with debounce.
- Cooldown guard to prevent repeat clicks.
- Only clicks elements that are:
  - visible,
  - enabled,
  - and inside configured container selector.
- Overlay indicator in-page:
  - shows active state,
  - mode (dry-run/live),
  - last click timestamp.
- Toolbar popup:
  - global enable toggle,
  - per-site enable toggle,
  - dry-run toggle,
  - status preview.
- Options page:
  - URL allowlist patterns,
  - button text patterns,
  - container selector,
  - cooldown/debounce tuning.

## Install (Developer Mode)

1. Open `chrome://extensions` or `edge://extensions`.
2. Enable Developer mode.
3. Click Load unpacked.
4. Select this `extension/` folder.
5. Open extension Options and configure your allowlist before enabling.

## Build Upload ZIP

From repo root:

```powershell
.\scripts\package_extension.ps1
```

This generates:

`release\out\submit-autoclicker-extension-upload.zip`

## Pattern Examples

Allowlist URL patterns:

- `https://github.com/*`
- `https://*.example.com/forms/*`
- `http://localhost:3000/*`

Button patterns:

- `Submit`
- `Continue`
- `Apply`

## Notes

- The extension never clicks non-allowlisted URLs.
- Keep cooldown conservative for production pages with re-renders.
- Use dry-run when introducing a new site pattern.

## Publish to Chrome/Edge Stores

1. Prepare listing copy from `docs/store/chrome_web_store_listing.md`.
2. Follow API/manual flow in `docs/store/chrome_publish_step_by_step.md`.
3. Publish privacy policy from `docs/privacy/privacy-policy.md` to a public URL.
4. Build screenshots showing:
   - popup toggles,
   - options allowlist,
   - in-page active overlay.
5. Submit to Chrome Web Store and Edge Add-ons.

## Metadata

- Name: `Submit Auto-Clicker (Safe)`
- Manifest description is already optimized for store/search relevance.
- `homepage_url` points to the GitHub repo.
