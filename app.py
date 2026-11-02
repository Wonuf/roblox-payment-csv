"""Roblox Payout CSV Generator.

Runs a small local web server, opens the UI in the default browser, and
proxies Roblox user lookups (browsers can't call the Roblox API directly).
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_NAME = "RobloxPayoutCSV"
PREFERRED_PORT = 8765


def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def state_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, APP_NAME)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "state.json")


def roblox_post(url, payload, attempts=3):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"{APP_NAME}/1.0",
        },
        method="POST",
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            # Roblox rate-limits these endpoints; back off and retry.
            if e.code == 429 and attempt < attempts - 1:
                time.sleep(2 * (attempt + 1))
                continue
            if e.code == 429:
                raise RuntimeError("Roblox is rate limiting lookups - wait a few seconds and click Re-check users") from e
            raise RuntimeError(f"Roblox returned HTTP {e.code}") from e


def lookup_users(ids, names):
    """Return {"byId": {id: {...}}, "byName": {lowername: {...}}}."""
    result = {"byId": {}, "byName": {}}
    if ids:
        data = roblox_post("https://users.roblox.com/v1/users", {"userIds": ids, "excludeBannedUsers": False})
        for u in data.get("data", []):
            result["byId"][str(u["id"])] = {"id": u["id"], "name": u["name"], "displayName": u.get("displayName")}
    if names:
        data = roblox_post("https://users.roblox.com/v1/usernames/users", {"usernames": names, "excludeBannedUsers": False})
        for u in data.get("data", []):
            key = u.get("requestedUsername", u["name"]).lower()
            result["byName"][key] = {"id": u["id"], "name": u["name"], "displayName": u.get("displayName")}
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(resource_path("index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/state":
            try:
                with open(state_path(), encoding="utf-8") as f:
                    self.send_json(json.load(f))
            except (FileNotFoundError, json.JSONDecodeError):
                self.send_json({})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/state":
            with open(state_path(), "w", encoding="utf-8") as f:
                json.dump(self.read_json(), f, indent=2)
            self.send_json({"ok": True})
        elif self.path == "/api/lookup":
            body = self.read_json()
            ids = [int(i) for i in body.get("ids", [])][:100]
            names = [str(n) for n in body.get("names", [])][:100]
            try:
                self.send_json(lookup_users(ids, names))
            except RuntimeError as e:
                self.send_json({"error": str(e)}, 502)
            except (urllib.error.URLError, TimeoutError, ValueError) as e:
                self.send_json({"error": f"Couldn't reach Roblox ({e}) - check your internet connection"}, 502)
        else:
            self.send_error(404)


def make_server():
    try:
        return ThreadingHTTPServer(("127.0.0.1", PREFERRED_PORT), Handler)
    except OSError:
        # Preferred port busy (maybe the app is already open) - use any free port.
        return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


def main():
    server = make_server()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Roblox Payout CSV Generator running at {url}")
    print("Close this window to quit.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
