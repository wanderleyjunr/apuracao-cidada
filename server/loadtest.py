"""Load test of the consumer path (the real bottleneck; reads are static on the CDN).

Simulates election night for real MG sections: TSE side preloaded (as the mirror would), then door ballots arrive
in consumer-sized batches (3 witnesses per section, ~1% divergent), each batch = ingest + one recompute per section.
Target: >= 105 submissions/s sustained (1.5M submissions in 4h; the queue absorbs the ~1k/s peak).
Run:  DATABASE_URL=postgresql://postgres:dev@localhost:55433/postgres uv run python loadtest.py [sections=5000] [batch=50]
Uses its own database (confere_load), recreated on every run.
"""
import json
import os
import random
import sys
import time
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from confere.ballot import assemble
from confere.pipeline import ingest_submission, recompute
from confere.synthetic import make, p521_key_and_cert

ROOT = Path(__file__).parents[1]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
BATCH = int(sys.argv[2]) if len(sys.argv) > 2 else 50
WITNESSES = 3


def sections(limit: int):
    for f in sorted((ROOT / "app/public/results/1/mg").glob("*/*.json")):
        if f.name == "city.json":
            continue
        mun, zone = int(f.parent.name), int(f.stem)
        for sec, data in json.loads(f.read_text())["sections"].items():
            yield mun, zone, int(sec), data
            limit -= 1
            if not limit:
                return


def main():
    base = os.environ["DATABASE_URL"]
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute("DROP DATABASE IF EXISTS confere_load")
        admin.execute("CREATE DATABASE confere_load")
    conn = psycopg.connect(psycopg.conninfo.make_conninfo(base, dbname="confere_load"), autocommit=True)
    conn.execute((ROOT / "server/schema.sql").read_text())

    secs = list(sections(N))
    t0 = time.perf_counter()
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO tse_ballots (section_key, file_hash, received_at, votes) VALUES (%s, 'load', %s, %s)",
                        [(f"1:mg:{m}:{z}:{s}", d["received"], Jsonb(d["votes"])) for m, z, s, d in secs])
    print(f"preload TSE side: {len(secs)} sections in {time.perf_counter() - t0:.1f}s")

    random.seed(1)
    msgs = []
    for m, z, s, d in secs:
        votes = json.loads(json.dumps(d["votes"]))
        if random.random() < 0.01:  # ~1% divergent
            k = next(k for k in votes["1"] if k.isdigit())
            votes["1"][k] += 1
        texts = make("mg", m, z, s, votes, signer=p521_key_and_cert())  # every urna signs (P-521, worst realistic case we can test)
        msgs += [{"texts": texts, "sectionKey": f"1:mg:{m}:{z}:{s}", "rawKey": "load", "receivedAt": "2026-10-25T20:30:00Z", "ipHash": f"ip{w}"}
                 for w in range(WITNESSES)]
    random.shuffle(msgs)

    t0 = time.perf_counter()
    assemble_s = 0.0
    for i in range(0, len(msgs), BATCH):  # same shape as run.consume_forever
        touched = set()
        for msg in msgs[i:i + BATCH]:
            a = time.perf_counter(); assemble(msg["texts"]); assemble_s += time.perf_counter() - a
            touched.add(ingest_submission(conn, msg))
        for key in touched:
            recompute(conn, key)
    elapsed = time.perf_counter() - t0
    rate = len(msgs) / elapsed
    status = dict(conn.execute("SELECT status, count(*) FROM latest_comparisons GROUP BY 1").fetchall())
    print(f"{len(msgs)} submissions in {elapsed:.1f}s → {rate:.0f}/s (target ≥105/s) · assemble {assemble_s / len(msgs) * 1000:.2f} ms each")
    sig = dict(conn.execute("SELECT signature_status, count(*) FROM ballots GROUP BY 1").fetchall())
    print(f"signatures: {sig}")
    print(f"verdicts: {status} · 1.5M submissions would take {1_500_000 / rate / 3600:.1f}h on one consumer")


if __name__ == "__main__":
    main()
