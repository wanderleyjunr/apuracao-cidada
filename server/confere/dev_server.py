"""Local stand-in for edge/ + queue + publisher (no Cloudflare, no cost):  uv run python -m confere.dev_server

POST /api/ballots {texts} → same pipeline as production (assemble → ingest → recompute) → writes the public section
document to <PUBLIC_DIR>/sections/<turn>/<uf>/<mun>/<zone>/<section>.json, where the app reads it.
The TSE side comes from the official per-zone results already in <PUBLIC_DIR>/results (bweb), seeded on demand.
Env: DATABASE_URL (default local docker), PUBLIC_DIR (default ../app/public), PORT (default 8787), ALLOW_TEST_BALLOTS=1.
ponytail: single-threaded DB connection and no rate limit — dev only; production ingest is edge/ (rate limit, queue).
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

import psycopg
from psycopg.types.json import Jsonb

from .ballot import BallotError, assemble
from . import public_log
from .aggregates import publish_local
from .alerts import notify
from .pipeline import ingest_submission, recompute, section_path

PUBLIC = Path(os.environ.get("PUBLIC_DIR", Path(__file__).parents[2] / "app/public"))
DB = os.environ.get("DATABASE_URL", "postgresql://postgres:dev@localhost:55433/postgres")
ALLOW_TEST = os.environ.get("ALLOW_TEST_BALLOTS") == "1"
lock = Lock()
conn: psycopg.Connection | None = None


def seed_tse(c: psycopg.Connection, key: str) -> None:
    """Loads the TSE side of a section from results/<turn>/<uf>/<mun>/<zone>.json if not in the DB yet."""
    turn, uf, mun, zone, section = key.split(":")
    if c.execute("SELECT 1 FROM tse_ballots WHERE section_key = %s", (key,)).fetchone():
        return
    f = PUBLIC / "results" / turn / uf / mun / f"{zone}.json"
    sec = json.loads(f.read_text())["sections"].get(section) if f.exists() else None
    if sec:
        c.execute("INSERT INTO tse_ballots (section_key, file_hash, received_at, votes) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                  (key, "bweb", sec["received"], Jsonb(sec["votes"])))


def handle(texts: list, ip: str) -> tuple[int, dict]:
    try:
        b = assemble(texts)
    except BallotError as e:
        return 422, {"error": str(e)}
    if not (b.is_official_2026() or ALLOW_TEST):
        return 422, {"error": "Só boletins oficiais de 2026 entram na conferência."}
    key = b.section_key()
    msg = {"texts": b.texts, "sectionKey": key, "rawKey": f"dev/{b.final_hash}.json", "receivedAt": datetime.now(timezone.utc).isoformat(),
           "ipHash": hashlib.sha256(f"{ip}|{datetime.now().date()}".encode()).hexdigest()}
    with lock:
        ingest_submission(conn, msg)
        seed_tse(conn, key)
        doc = recompute(conn, key)
        if doc:
            out = PUBLIC / section_path(key)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(doc, ensure_ascii=False))
            # zone index {section: status} so the zone view needs one request, not one per section
            index = out.parent.with_suffix(".json")
            statuses = json.loads(index.read_text()) if index.exists() else {}
            statuses[key.rsplit(":", 1)[1]] = doc["status"]
            index.write_text(json.dumps(statuses))
            publish_local(conn, int(key.split(":")[0]), PUBLIC)  # ponytail: per submission is fine locally; prod runs it on a timer
        public_log.publish_local(conn, int(key.split(":")[0]), PUBLIC)  # local: no OpenTimestamps anchoring
    notify(doc, "http://localhost:5174")
    return 202, {"receipt": b.final_hash[:16], "section": key, "status": doc and doc["status"]}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict | None = None):
        self.send_response(status)
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-headers", "content-type")
        self.send_header("content-type", "application/json")
        self.end_headers()
        if body is not None:
            self.wfile.write(json.dumps(body, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self._send(204)

    def do_POST(self):
        if self.path != "/api/ballots":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("content-length", 0))
        if length > 64 * 1024:
            return self._send(413, {"error": "Envio grande demais."})
        try:
            texts = json.loads(self.rfile.read(length))["texts"]
            assert isinstance(texts, list) and all(isinstance(t, str) for t in texts) and 0 < len(texts) <= 40
        except Exception:
            return self._send(400, {"error": "Envie os textos dos QR Codes do boletim."})
        self._send(*handle(texts, self.client_address[0]))


def main():
    global conn
    conn = psycopg.connect(DB, autocommit=True)
    conn.execute((Path(__file__).parents[1] / "schema.sql").read_text())
    port = int(os.environ.get("PORT", 8787))
    print(f"dev ingest on http://localhost:{port}/api/ballots → {PUBLIC}/sections")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
