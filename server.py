#!/usr/bin/env python3
"""Tiny local server: serves the commentary site and accepts annotations (POST /api/comment)."""

import json
import os
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import build_site

HERE = os.path.dirname(os.path.abspath(__file__))
COMMENTS = os.path.join(HERE, "data", "comments.jsonl")
PORT = int(os.environ.get("PORT", "8787"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def log_message(self, fmt, *args):  # quieter logs
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_POST(self):
        if self.path.rstrip("/") != "/api/comment":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            item_id = str(payload.get("item_id", "")).strip()
            text = str(payload.get("text", "")).strip()
            name = str(payload.get("name", "")).strip() or "匿名"
            if not item_id or not text:
                raise ValueError("item_id and text required")
            record = {
                "item_id": item_id,
                "name": name[:40],
                "text": text[:2000],
                "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            }
            os.makedirs(os.path.dirname(COMMENTS), exist_ok=True)
            with open(COMMENTS, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            build_site.main()
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:  # noqa: BLE001
            body = json.dumps({"ok": False, "error": str(exc)}).encode()
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    build_site.main()
    print(f"serving http://localhost:{PORT}/")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
