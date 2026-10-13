"""Long-running worker for the Brazil VPS:  uv run python -m confere.run [consume|mirror|all]

Env: DATABASE_URL, EDGE_URL, PUBLISH_TOKEN, CF_ACCOUNT_ID, CF_QUEUE_ID, CF_API_TOKEN,
     PUBLIC_URL (app URL used in alerts), OBSERVER_WEBHOOKS, TURN (1|2, default 2), PLACES_DIR (default ../app/public/places), MIRROR_ROOT (default ./mirror), MIRROR_UFS (default all), MIRROR_INTERVAL_S (default 60).
"""
import asyncio
import base64
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx
import psycopg

from . import public_log
from .aggregates import coverage, divergences, place_index
from .alerts import notify
from .ballot import BallotError
from .pipeline import ingest_submission, ingest_tse, publish, recompute, section_path
from .tse_mirror import ELECTION, UFS, Mirror, Section

log = logging.getLogger("confere")
CF_API = "https://api.cloudflare.com/client/v4/accounts/{account}/queues/{queue}/messages"


def decode_body(body) -> dict:
    """Pull-consumer bodies arrive as JSON or base64 depending on content type (ponytail: handle both)."""
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return json.loads(base64.b64decode(body))


def _publish(doc: dict | None, http: httpx.Client) -> None:
    if doc:
        publish(os.environ["EDGE_URL"], os.environ["PUBLISH_TOKEN"], section_path(doc["key"]), doc, http)


def consume_forever(batch: int = 50) -> None:
    url = CF_API.format(account=os.environ["CF_ACCOUNT_ID"], queue=os.environ["CF_QUEUE_ID"])
    headers = {"authorization": f"Bearer {os.environ['CF_API_TOKEN']}"}
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn, httpx.Client(timeout=30) as http:
        while True:
            r = http.post(f"{url}/pull", headers=headers, json={"batch_size": batch, "visibility_timeout_ms": 60000})
            r.raise_for_status()
            messages = r.json()["result"]["messages"]
            if not messages:
                time.sleep(1)
                continue
            acks, retries, touched = [], [], set()
            for m in messages:
                try:
                    touched.add(ingest_submission(conn, decode_body(m["body"])))
                    acks.append({"lease_id": m["lease_id"]})
                except BallotError as e:  # invalid at the source: drop, never retry
                    log.warning("dropped invalid ballot: %s", e)
                    acks.append({"lease_id": m["lease_id"]})
                except Exception:
                    log.exception("retrying message")
                    retries.append({"lease_id": m["lease_id"]})
            for key in touched:  # one recompute per section per batch
                doc = recompute(conn, key)
                _publish(doc, http)
                notify(doc, os.environ.get("PUBLIC_URL", ""))
            http.post(f"{url}/ack", headers=headers, json={"acks": acks, "retries": retries}).raise_for_status()


async def mirror_forever() -> None:
    turn = int(os.environ.get("TURN", 2))
    pleito = ELECTION[turn]
    ufs = os.environ.get("MIRROR_UFS", " ".join(UFS)).split()
    mirror = Mirror(Path(os.environ.get("MIRROR_ROOT", "mirror")))
    conn = await asyncio.to_thread(psycopg.connect, os.environ["DATABASE_URL"], autocommit=True)
    http = httpx.Client(timeout=30)

    def on_ballot(s: Section, bu_path: Path) -> None:
        aux = json.loads((bu_path.parent / "aux.json").read_text())["hashes"][-1]
        key = ingest_tse(conn, s.key(turn), aux["hash"], f"{aux['dr']} {aux['hr']}", bu_path.read_bytes())
        _publish(recompute(conn, key), http)

    last_checkpoint = 0.0
    while True:
        for uf in ufs:
            try:
                n = await mirror.sync_uf(pleito, uf, on_ballot)
                log.info("mirror %s: %d sections updated", uf, n)
            except Exception:
                log.exception("mirror %s failed; will retry next pass", uf)
        totals, names = place_index(Path(os.environ.get("PLACES_DIR", "../app/public/places")))
        for name, doc in (("coverage", coverage(conn, turn, totals)), ("divergences", divergences(conn, turn, names))):
            publish(os.environ["EDGE_URL"], os.environ["PUBLISH_TOKEN"], f"aggregates/{turn}/{name}.json", doc, http)
        if time.time() - last_checkpoint > 3600:  # hourly public-log checkpoint, anchored in OpenTimestamps
            await asyncio.to_thread(publish_log, conn, turn, http)
            last_checkpoint = time.time()
        await asyncio.sleep(int(os.environ.get("MIRROR_INTERVAL_S", 60)))


def publish_log(conn, turn: int, http: httpx.Client) -> None:
    """Builds the log locally, then pushes every page + checkpoints.json through the edge."""
    root = Path(os.environ.get("MIRROR_ROOT", "mirror")) / "public"
    if public_log.publish_local(conn, turn, root, do_anchor=True):
        for f in sorted((root / "log" / str(turn)).glob("*.json")):
            publish(os.environ["EDGE_URL"], os.environ["PUBLISH_TOKEN"], f"log/{turn}/{f.name}", json.loads(f.read_text()), http)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode == "consume":
        consume_forever()
    elif mode == "mirror":
        asyncio.run(mirror_forever())
    else:
        async def both():
            await asyncio.gather(asyncio.to_thread(consume_forever), mirror_forever())
        asyncio.run(both())


if __name__ == "__main__":
    main()
