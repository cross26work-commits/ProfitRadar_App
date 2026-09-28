"""Loopback-only redirect bridge for the gitignored Stripe Checkout URL."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit


STATE = Path(__file__).resolve().parents[2] / ".local-isolated" / "stripe-e2e-state.json"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/checkout":
            self.send_error(404)
            return
        url = str(json.loads(STATE.read_text(encoding="utf-8")).get("checkout_url") or "")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "checkout.stripe.com":
            self.send_error(503)
            return
        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8022), Handler).serve_forever()
