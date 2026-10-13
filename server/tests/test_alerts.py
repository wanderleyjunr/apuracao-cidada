import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from confere.alerts import notify

DOC = {"key": "2:ac:1392:9:17", "status": "divergent", "differences": [{"key": "3:11", "door": 128, "tse": 130}], "opened": True}


def test_notify_posts_only_when_divergence_opens():
    got = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            got.append(json.loads(self.rfile.read(int(self.headers["content-length"]))))
            self.send_response(200); self.end_headers()

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}/hook"
    assert notify({**DOC, "opened": False}, webhooks=url) == 0
    assert notify(DOC, "https://confere.example", webhooks=url) == 1
    assert "3:11: porta 128 × TSE 130" in got[0]["text"] and "não acusação" in got[0]["text"]
    assert notify(DOC, webhooks="http://127.0.0.1:1/down") == 0  # failing webhook never raises
