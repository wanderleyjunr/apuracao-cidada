"""Public append-only log of every submission: a hash chain anyone can recompute.

entry_i = sha256(entry_{i-1} | final_hash | section_key | received_at)   (entry_0 = 64 zeros)
Published: log/<turn>/page-<k>.json (1000 entries each: [id, final_hash, section_key, received_at, chain]) and
log/<turn>/checkpoints.json (append-only list of {count, head, at, ots?}). A checkpoint proves that every ballot up to
`count` existed at `at`; anchoring `head` in OpenTimestamps makes `at` independent of us.
No IP hash or anything personal goes into the log. Verify: uv run python -m confere.public_log verify <log dir>
ponytail: pages are rewritten on each publish (fine hourly up to a few million rows); switch to tiles if it grows.
"""
import base64
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ZERO = "0" * 64
PAGE = 1000
OTS_CALENDAR = "https://a.pool.opentimestamps.org/digest"


def link(prev: str, final_hash: str, key: str, received_at: str) -> str:
    return hashlib.sha256(f"{prev}|{final_hash}|{key}|{received_at}".encode()).hexdigest()


def chain(rows) -> list[list]:
    """rows: (id, final_hash, section_key, received_at iso) ordered by id → entries with their chain hash."""
    out, prev = [], ZERO
    for id_, h, key, at in rows:
        prev = link(prev, h.strip(), key, at)
        out.append([id_, h.strip(), key, at, prev])
    return out


def verify(entries: list[list], checkpoint: dict) -> bool:
    """True if the entries recompute to the checkpoint head (and nothing before it was altered or removed)."""
    prev = ZERO
    for i, (_, h, key, at, stated) in enumerate(entries[: checkpoint["count"]]):
        prev = link(prev, h, key, at)
        if prev != stated:
            return False
    return checkpoint["count"] <= len(entries) and prev == checkpoint["head"]


def anchor(head: str) -> str | None:
    """Submits the head digest to an OpenTimestamps calendar; returns the (pending) proof in base64. Sends only a hash."""
    try:
        req = urllib.request.Request(OTS_CALENDAR, data=bytes.fromhex(head), headers={"accept": "application/vnd.opentimestamps.v1"})
        return base64.b64encode(urllib.request.urlopen(req, timeout=10).read()).decode()
    except OSError:
        return None  # anchoring is best effort; the checkpoint is still published


def publish_local(conn, turn: int, public: Path, do_anchor: bool = False) -> dict | None:
    rows = conn.execute(
        "SELECT id, final_hash, section_key, to_char(received_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"') "
        "FROM submissions WHERE section_key LIKE %s ORDER BY id", (f"{turn}:%",)).fetchall()
    if not rows:
        return None
    entries = chain(rows)
    out = public / "log" / str(turn)
    out.mkdir(parents=True, exist_ok=True)
    for k in range(0, len(entries), PAGE):
        (out / f"page-{k // PAGE}.json").write_text(json.dumps(entries[k:k + PAGE]))
    cps_path = out / "checkpoints.json"
    cps = json.loads(cps_path.read_text()) if cps_path.exists() else []
    head = entries[-1][4]
    if cps and cps[-1]["head"] == head:
        return cps[-1]
    cp = {"count": len(entries), "head": head, "at": datetime.now(timezone.utc).isoformat(), "pages": -(-len(entries) // PAGE)}
    if do_anchor and (proof := anchor(head)):
        cp["ots"] = proof
    cps.append(cp)
    cps_path.write_text(json.dumps(cps, indent=1))
    return cp


if __name__ == "__main__" and sys.argv[1:2] == ["verify"]:
    d = Path(sys.argv[2])
    cps = json.loads((d / "checkpoints.json").read_text())
    entries = [e for p in sorted(d.glob("page-*.json"), key=lambda p: int(p.stem.split("-")[1])) for e in json.loads(p.read_text())]
    ok = all(verify(entries, cp) for cp in cps)
    print(f"{len(entries)} entries, {len(cps)} checkpoints: {'OK' if ok else 'MISMATCH'}")
    sys.exit(0 if ok else 1)
