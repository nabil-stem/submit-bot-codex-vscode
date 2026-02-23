from __future__ import annotations

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    index = root / "index.html"
    if not index.exists():
        raise FileNotFoundError(f"Missing {index}")

    handler = SimpleHTTPRequestHandler
    server = HTTPServer(("0.0.0.0", 3000), handler)
    print("Replit landing page running on http://0.0.0.0:3000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

