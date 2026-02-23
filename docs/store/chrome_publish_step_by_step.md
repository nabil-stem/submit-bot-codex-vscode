# Chrome Web Store Publish: Step by Step

## One-Time Setup (Required)

1. Create/register Chrome Web Store developer account.  
2. Create a Google Cloud OAuth client (Desktop app is fine).  
3. Enable the **Chrome Web Store API** in your Google Cloud project.  
4. In Chrome Web Store Dashboard, create your extension item (first-time new item), complete:
   - Store listing tab
   - Privacy tab
   - Distribution tab
5. Note your:
   - `publisher_id`
   - `item_id` (extension ID)

For first publish, dashboard completion is required before API publish works reliably.

## Package the ZIP

From repo root:

```powershell
.\scripts\package_extension.ps1
```

Output:

`release\out\submit-autoclicker-extension-upload.zip`

## API Credentials

Set these environment variables in PowerShell:

```powershell
$env:CWS_PUBLISHER_ID = "your_publisher_id"
$env:CWS_ITEM_ID = "your_extension_item_id"
$env:CWS_CLIENT_ID = "your_google_oauth_client_id"
$env:CWS_CLIENT_SECRET = "your_google_oauth_client_secret"
$env:CWS_REFRESH_TOKEN = "your_oauth_refresh_token"
```

## Publish Command (Automated)

```powershell
python .\scripts\publish_chrome_web_store.py
```

Useful modes:

```powershell
# upload only
python .\scripts\publish_chrome_web_store.py --skip-publish

# check status only
python .\scripts\publish_chrome_web_store.py --status-only
```

## Listing Content

Use drafts from:

- `docs/store/chrome_web_store_listing.md`
- `docs/privacy/privacy-policy.md`

## Post-Publish

1. Add store URL to `marketing/launch_config.json`.
2. Regenerate launch copy:

```powershell
python .\scripts\generate_launch_kit.py --config .\marketing\launch_config.json --output .\marketing\out
```

