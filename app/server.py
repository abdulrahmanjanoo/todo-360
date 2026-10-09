"""Local server: the Obsidian vault is the live data source, this page is the desk.

    python3 app/server.py        then open http://127.0.0.1:8360

Binds to 127.0.0.1 only. Standard library only.
"""
import json
import os
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decisions  # noqa: E402
import export  # noqa: E402
from config import HERE, owner_me, port, vault_name, vault_path  # noqa: E402

STATIC = os.path.join(HERE, "static")
_cache = {"at": 0, "snap": None}
_cache_lock = threading.Lock()


def snapshot(force=False):
    with _cache_lock:
        if force or not _cache["snap"] or time.time() - _cache["at"] > 20:
            _cache["snap"] = export.build(vault_path())
            _cache["at"] = time.time()
        snap = dict(_cache["snap"])
    snap["decisions"] = decisions.load()
    snap["vault_name"] = vault_name()
    snap["me"] = owner_me()
    return snap


def safe_note(rel):
    """Only markdown under the transcript folder, never outside the vault."""
    root = os.path.realpath(vault_path())
    full = os.path.realpath(os.path.join(root, rel or ""))
    allowed = os.path.join(root, export.NOTES) + os.sep
    if not full.startswith(allowed) or not full.endswith(".md") or not os.path.isfile(full):
        return None
    with open(full, encoding="utf-8") as f:
        return f.read()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                with open(os.path.join(STATIC, "index.html"), "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            if u.path == "/api/snapshot":
                return self._send(200, snapshot(force="refresh" in q))
            if u.path == "/api/note":
                text = safe_note(q.get("file", [""])[0])
                return self._send(200, {"text": text}) if text is not None else self._send(404, {"error": "note not found"})
            return self._send(404, {"error": "not found"})
        except Exception as e:  # surface vault problems in the UI instead of a blank page
            return self._send(500, {"error": "%s: %s" % (type(e).__name__, e)})

    def do_POST(self):
        u = urlparse(self.path)
        # same-origin only: the page is served from here
        origin = self.headers.get("Origin")
        if origin and not origin.startswith(("http://127.0.0.1", "http://localhost")):
            return self._send(403, {"error": "forbidden"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            if u.path == "/api/decision":
                d = decisions.record(body.get("kind"), body.get("id"), body.get("action"),
                                     until=body.get("until"), note=body.get("note"))
                return self._send(200, {"decisions": d})
            if u.path == "/api/apply":
                res = decisions.apply(dry_run=bool(body.get("dry_run")))
                snapshot(force=True)
                return self._send(200, res)
            return self._send(404, {"error": "not found"})
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        except Exception as e:
            return self._send(500, {"error": "%s: %s" % (type(e).__name__, e)})


def main():
    vp = vault_path()
    if not os.path.isfile(os.path.join(vp, "Wiki", ".state", "todos.json")):
        sys.exit("Vault not found at %s. Set \"vault\" in config.json or TODO360_VAULT." % vp)
    p = port()
    srv = ThreadingHTTPServer(("127.0.0.1", p), Handler)
    url = "http://127.0.0.1:%d/" % p
    print("To-Do 360 on %s  (vault: %s)" % (url, vp))
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
