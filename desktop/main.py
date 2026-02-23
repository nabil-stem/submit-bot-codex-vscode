from __future__ import annotations

import argparse
from pathlib import Path

from submit_autoclicker.app import DesktopAutoClickerApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit Auto-Clicker (Windows Desktop)")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config TOML file. If omitted, uses %%APPDATA%%\\SubmitAutoClicker\\config.toml",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = DesktopAutoClickerApp(config_path=args.config)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())

