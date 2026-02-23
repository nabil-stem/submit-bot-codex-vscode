# Post-Approval Launch Checklist

Use this immediately after your Chrome Web Store listing is approved.

## 1) Add install link in README

Replace `YOUR_CHROME_STORE_URL` with your final listing URL.

```md
[![Chrome Web Store](https://img.shields.io/badge/Chrome_Web_Store-Install-1a73e8?logo=googlechrome&logoColor=white)](YOUR_CHROME_STORE_URL)
```

## 2) Add demo media

- Record a 15-30 second GIF/video:
  - open popup
  - show allowlist URL configured
  - keep dry-run enabled
  - show overlay "Auto-click active"
- If no GIF yet, use screenshot:
  - `marketing/store_assets/screenshot-04-overlay-active-1280x800.png`

## 3) Regenerate launch copy

Set `extension_store_url` in `marketing/launch_config.json`, then run:

```powershell
python .\scripts\generate_launch_kit.py --config .\marketing\launch_config.json --output .\marketing\out
```

## 4) Publish distribution posts

Use these files:

- `marketing/out/x_post.txt`
- `marketing/out/linkedin_post.md`
- `marketing/out/reddit_post.md`
- `marketing/out/devto_article.md`

## 5) Track conversion

- Add UTM links in posts.
- Check weekly:
  - store installs
  - GitHub stars
  - issue feedback quality
