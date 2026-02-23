from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote_plus


def load_config(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("launch config must be a JSON object")
    return data


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def val(data: dict[str, object], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return str(value or default).strip()


def val_list(data: dict[str, object], key: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def with_utm(base_url: str, source: str, medium: str = "social", campaign: str = "launch") -> str:
    if not base_url:
        return ""
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}utm_source={quote_plus(source)}&utm_medium={quote_plus(medium)}&utm_campaign={quote_plus(campaign)}"


def write_text(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def build_outputs(config: dict[str, object]) -> dict[str, str]:
    project = val(config, "project_name", "Submit Bot")
    tagline = val(config, "tagline", "Safe auto-submit automation.")
    repo_url = val(config, "repo_url")
    extension_store_url = val(config, "extension_store_url")
    website_url = val(config, "website_url")
    cta = val(config, "primary_call_to_action", "Try it and share feedback.")
    keywords = val_list(config, "keywords")

    keywords_csv = ", ".join(keywords[:12])
    core_url = website_url or repo_url

    github_description = "Safe VS Code Codex + Chrome/Edge submit auto-clicker with allowlists, dry-run mode, and visible automation status."
    github_topics = [
        "vscode",
        "codex",
        "automation",
        "python",
        "ui-automation",
        "chrome-extension",
        "edge-extension",
        "autoclicker",
        "productivity",
        "windows11"
    ]

    outputs: dict[str, str] = {}
    outputs["github_description.txt"] = github_description
    outputs["github_topics.txt"] = "\n".join(github_topics)
    outputs["github_about.md"] = (
        f"### Recommended GitHub About\n\n"
        f"- **Description**: {github_description}\n"
        f"- **Website**: {core_url or '(set your website/release URL)'}\n"
        f"- **Topics**: {', '.join(github_topics)}\n"
    )

    outputs["x_post.txt"] = (
        f"{project} is live.\n\n"
        f"{tagline}\n"
        f"- Windows desktop (UIA-first)\n"
        f"- Chrome/Edge extension (MV3)\n"
        f"- Allowlists + dry-run + cooldown + visible status\n\n"
        f"Repo: {with_utm(repo_url, 'x')}\n"
        f"{cta}\n\n"
        f"#{' #'.join([k.replace(' ', '') for k in keywords[:4]])}"
    )

    outputs["linkedin_post.md"] = (
        f"## {project} is available\n\n"
        f"{tagline}\n\n"
        f"I built this with production guardrails:\n"
        f"- Safe-by-default allowlists\n"
        f"- Dry-run mode before live actions\n"
        f"- Global pause/resume + visible active indicator\n"
        f"- Configurable cooldown and filters\n\n"
        f"Open source repo: {with_utm(repo_url, 'linkedin')}\n"
        f"Keywords: {keywords_csv}\n\n"
        f"{cta}\n\n"
        f"#opensource #automation #vscode #chromeextension"
    )

    outputs["reddit_post.md"] = (
        f"Title: I built a safe submit auto-clicker for VS Code Codex + Chrome/Edge\n\n"
        f"Hi all, I built **{project}**.\n\n"
        f"Key points:\n"
        f"- Safe by default (allowlist only)\n"
        f"- Dry-run mode to validate behavior\n"
        f"- Windows desktop mode (UI Automation)\n"
        f"- Browser extension mode (MV3, URL-scoped)\n\n"
        f"Repo: {with_utm(repo_url, 'reddit')}\n"
        f"{cta}\n\n"
        f"Happy to take feedback on edge cases and reliability."
    )

    outputs["devto_article.md"] = (
        f"# {project}: Safe Auto-Submit for VS Code and Browser Workflows\n\n"
        f"{tagline}\n\n"
        f"## Why I built it\n"
        f"I needed automation that does not randomly click unknown prompts. "
        f"This project is allowlist-first, observable, and testable.\n\n"
        f"## What it includes\n"
        f"- Desktop mode: Python + UIA first, optional image fallback.\n"
        f"- Extension mode: Chrome/Edge MV3 with MutationObserver and cooldown.\n"
        f"- Shared safety rules: allowlist, dry-run, visible active state.\n\n"
        f"## Repo\n"
        f"{with_utm(repo_url, 'devto')}\n\n"
        f"## Keywords\n"
        f"{keywords_csv}\n"
    )

    outputs["producthunt_copy.md"] = (
        f"# Product Hunt Listing Draft\n\n"
        f"## Name\n{project}\n\n"
        f"## Tagline\n{tagline}\n\n"
        f"## Description\n"
        f"Automate submit actions safely in VS Code Codex and selected web pages. "
        f"Uses strict allowlists, dry-run mode, cooldowns, and clear active indicators.\n\n"
        f"## Links\n"
        f"- Repo: {with_utm(repo_url, 'producthunt')}\n"
        f"- Website: {with_utm(website_url, 'producthunt') if website_url else '(set website URL)'}\n"
        f"- Extension: {extension_store_url or '(set Chrome Web Store URL)'}\n"
    )

    outputs["hackernews_submission.txt"] = (
        f"Title: Show HN: {project} (safe auto-submit for VS Code Codex + Chrome/Edge)\n"
        f"URL: {with_utm(repo_url, 'hackernews')}\n"
        f"Text: {tagline} Built with allowlist-only execution, dry-run mode, cooldowns, and visible status."
    )

    outputs["chrome_store_short_description.txt"] = (
        "Allowlist-based submit auto-clicker with dry-run safeguards for selected websites."
    )

    outputs["replit_showcase_post.md"] = (
        f"# Replit Showcase Copy\n\n"
        f"Project: {project}\n\n"
        f"Use Replit to host a landing/demo page that links to:\n"
        f"- GitHub repo: {with_utm(repo_url, 'replit')}\n"
        f"- Extension listing: {extension_store_url or '(set extension URL)'}\n\n"
        f"Note: the desktop Windows automation runtime itself should run on Windows, not in Replit."
    )

    outputs["launch_checklist.md"] = (
        f"# Launch Checklist ({project})\n\n"
        f"1. Update GitHub About description/topics using `github_about.md`.\n"
        f"2. Push a tagged release and attach ZIP artifacts.\n"
        f"3. Publish Chrome/Edge listing using docs in `docs/store/`.\n"
        f"4. Publish one post per platform (X, LinkedIn, Reddit, Dev.to, HN).\n"
        f"5. Track UTM links and conversion weekly.\n"
        f"6. Iterate with changelog + reliability metrics.\n"
    )

    outputs["anti_spam_note.txt"] = (
        "Post manually and adapt copy per community rules. Avoid repetitive or automated bulk posting."
    )

    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate launch/SEO text kit for Submit Bot.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("marketing/launch_config.json"),
        help="Path to launch config JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("marketing/out"),
        help="Output folder for generated launch copy",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    ensure_dir(args.output)
    outputs = build_outputs(config)

    for filename, content in outputs.items():
        write_text(args.output / filename, content)

    print(f"Generated {len(outputs)} launch files in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
