# Release Packaging

Use the helper script to prepare distributable artifacts for both modes.

## Command

```powershell
.\scripts\build_release.ps1
```

Optional:

```powershell
.\scripts\build_release.ps1 -OutputDir .\release\out -NoZip
```

## Output

Generated under `release/out/`:

- `submit-autoclicker-desktop.zip`
- `submit-autoclicker-extension.zip`
- `submit-autoclicker-bundle.zip`
- `staging/` (expanded folder layout used for zips)

The packaging script excludes transient files such as `__pycache__`, `.pytest_cache`, and `.venv`.

