from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL_TMPL = "https://chromewebstore.googleapis.com/upload/v2/publishers/{publisher_id}/items/{item_id}:upload"
PUBLISH_URL_TMPL = "https://chromewebstore.googleapis.com/v2/publishers/{publisher_id}/items/{item_id}:publish"
STATUS_URL_TMPL = "https://chromewebstore.googleapis.com/v2/publishers/{publisher_id}/items/{item_id}:fetchStatus"


def _require(value: str | None, name: str) -> str:
    if value and value.strip():
        return value.strip()
    raise ValueError(f"Missing required value: {name}")


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> dict[str, Any]:
    req = urllib.request.Request(url=url, method=method, headers=headers or {}, data=data)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="replace").strip()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {exc.reason} for {url}\n{raw}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    payload = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    token = _request_json(
        TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=payload,
    )
    return _require(token.get("access_token"), "access_token")


def upload_package(access_token: str, publisher_id: str, item_id: str, zip_path: Path) -> dict[str, Any]:
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    url = UPLOAD_URL_TMPL.format(publisher_id=publisher_id, item_id=item_id)
    data = zip_path.read_bytes()
    return _request_json(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/zip",
        },
        data=data,
    )


def publish_item(access_token: str, publisher_id: str, item_id: str) -> dict[str, Any]:
    url = PUBLISH_URL_TMPL.format(publisher_id=publisher_id, item_id=item_id)
    return _request_json(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        data=b"{}",
    )


def fetch_status(access_token: str, publisher_id: str, item_id: str) -> dict[str, Any]:
    url = STATUS_URL_TMPL.format(publisher_id=publisher_id, item_id=item_id)
    return _request_json(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload and publish Chrome Web Store extension (API V2).")
    parser.add_argument("--zip", type=Path, default=Path("release/out/submit-autoclicker-extension-upload.zip"))
    parser.add_argument("--publisher-id", default=os.getenv("CWS_PUBLISHER_ID", ""))
    parser.add_argument("--item-id", default=os.getenv("CWS_ITEM_ID", ""))
    parser.add_argument("--client-id", default=os.getenv("CWS_CLIENT_ID", ""))
    parser.add_argument("--client-secret", default=os.getenv("CWS_CLIENT_SECRET", ""))
    parser.add_argument("--refresh-token", default=os.getenv("CWS_REFRESH_TOKEN", ""))
    parser.add_argument("--skip-upload", action="store_true", help="Skip upload and only publish/status.")
    parser.add_argument("--skip-publish", action="store_true", help="Upload only, do not publish.")
    parser.add_argument("--status-only", action="store_true", help="Only fetch status.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        publisher_id = _require(args.publisher_id, "--publisher-id or CWS_PUBLISHER_ID")
        item_id = _require(args.item_id, "--item-id or CWS_ITEM_ID")
        client_id = _require(args.client_id, "--client-id or CWS_CLIENT_ID")
        client_secret = _require(args.client_secret, "--client-secret or CWS_CLIENT_SECRET")
        refresh_token = _require(args.refresh_token, "--refresh-token or CWS_REFRESH_TOKEN")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        token = get_access_token(client_id, client_secret, refresh_token)
        print("Access token acquired.")

        if args.status_only:
            status = fetch_status(token, publisher_id, item_id)
            print(json.dumps({"status": status}, indent=2))
            return 0

        upload_resp: dict[str, Any] | None = None
        publish_resp: dict[str, Any] | None = None

        if not args.skip_upload:
            upload_resp = upload_package(token, publisher_id, item_id, args.zip)
            print("Upload response:")
            print(json.dumps(upload_resp, indent=2))

        if not args.skip_publish:
            publish_resp = publish_item(token, publisher_id, item_id)
            print("Publish response:")
            print(json.dumps(publish_resp, indent=2))

        status = fetch_status(token, publisher_id, item_id)
        print("Current item status:")
        print(json.dumps(status, indent=2))
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

