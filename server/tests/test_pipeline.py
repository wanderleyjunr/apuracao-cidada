"""Integration test against a real Postgres. Run with:
    docker run -d --rm --name confere-pg -e POSTGRES_PASSWORD=dev -p 55433:5432 postgres:17
    DATABASE_URL=postgresql://postgres:dev@localhost:55433/postgres uv run --group dev pytest tests/test_pipeline.py
Skipped when DATABASE_URL is not set.
"""
import json
import os
from pathlib import Path

import psycopg
import pytest

from confere.aggregates import coverage, divergences
from confere.pipeline import ingest_submission, ingest_tse, recompute, section_path

ROOT = Path(__file__).parents[2]
DB = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB, reason="DATABASE_URL not set")


@pytest.fixture
def conn():
    # own database: the test wipes its schema, so it must never touch the dev/prod database in DATABASE_URL
    with psycopg.connect(DB, autocommit=True) as admin:
        if not admin.execute("SELECT 1 FROM pg_database WHERE datname = 'confere_test'").fetchone():
            admin.execute("CREATE DATABASE confere_test")
    with psycopg.connect(psycopg.conninfo.make_conninfo(DB, dbname="confere_test"), autocommit=True) as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
        c.execute((ROOT / "server/schema.sql").read_text())
        yield c


def msg(texts, ip="a"):
    return {"texts": texts, "sectionKey": "1:zz:30198:1:265", "rawKey": "raw/x.json", "receivedAt": "2026-10-04T20:06:00Z", "ipHash": ip}


def test_door_then_tse_identical_and_divergent(conn):
    texts = next(t for t in json.loads((ROOT / "fixtures/ballots-2022-abroad.json").read_text()) if "SECA:265" in t[0])
    key = ingest_submission(conn, msg(texts, "a"))
    ingest_submission(conn, msg(texts, "b"))  # second witness
    doc = recompute(conn, key)
    assert doc["status"] == "waiting" and doc["door"]["submissions"] == 2 and doc["door"]["signature"] == "unverified"
    assert section_path(key) == "sections/1/zz/30198/1/265.json"

    # TSE side: reuse the real MG bu.dat but pretend it is this section → must diverge
    bu = (ROOT / "fixtures/tse-section-mg-53112-0170-0037/o03220mg5311201700037-bu.dat").read_bytes()
    ingest_tse(conn, key, "h-tse", "04/10/2026 18:47:10", bu)
    doc = recompute(conn, key)
    assert doc["status"] == "divergent" and doc["tse"]["receivedAt"] == "04/10/2026 18:47:10"
    assert conn.execute("SELECT kind FROM divergence_events").fetchall() == [("opened",)]
    recompute(conn, key)  # idempotent: no new comparison row when nothing changed
    assert conn.execute("SELECT count(*) FROM comparisons").fetchone()[0] == 2

    cov = coverage(conn, 1, {"zz": 4})
    assert cov["checked"] == 1 and cov["byStatus"]["divergent"] == 1 and cov["byUF"]["ZZ"] == 0.25
    div = divergences(conn, 1, {("zz", 30198): "NAGOIA"})["items"]
    assert [(d["municipality"], d["section"], d["status"]) for d in div] == [("NAGOIA", 265, "divergent")]
