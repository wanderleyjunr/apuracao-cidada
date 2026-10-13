"""Public aggregates from the DB: coverage (how much was checked) and the divergence list. No vote sums.

Published as aggregates/<turn>/coverage.json and aggregates/<turn>/divergences.json.
ponytail: denominators come from the place index (includes aggregated sections, ~3% that print no BU of their own);
swap for the TSE "sections with BU" count per UF if the percentage needs to be exact.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import psycopg

CHECKED = ("waiting", "identical", "divergent", "conflict")


def place_index(places_dir: Path) -> tuple[dict[str, int], dict[tuple[str, int], str]]:
    """({uf: total sections}, {(uf, municipality code): name}) from app/public/places/<uf>.json."""
    totals, names = {}, {}
    for f in places_dir.glob("*.json"):
        d = json.loads(f.read_text())
        totals[d["uf"]] = sum(len(s) for m in d["municipalities"] for s in m["zones"].values())
        names.update({(d["uf"], m["code"]): m["name"] for m in d["municipalities"]})
    return totals, names


def coverage(conn: psycopg.Connection, turn: int, totals: dict[str, int]) -> dict:
    rows = conn.execute(
        "SELECT split_part(section_key, ':', 2) AS uf, status, count(*) FROM latest_comparisons WHERE section_key LIKE %s GROUP BY 1, 2",
        (f"{turn}:%",)).fetchall()
    by_status = {s: 0 for s in CHECKED}
    per_uf: dict[str, int] = {}
    for uf, status, n in rows:
        if status in CHECKED:
            by_status[status] += n
            per_uf[uf] = per_uf.get(uf, 0) + n
    total = sum(totals.values()) or 1
    return {
        "turn": turn, "updatedAt": datetime.now(timezone.utc).isoformat(), "totalSections": total,
        "checked": sum(by_status.values()), "byStatus": by_status,
        "byUF": {uf.upper(): round(per_uf.get(uf, 0) / n, 4) for uf, n in sorted(totals.items()) if n},
    }


def divergences(conn: psycopg.Connection, turn: int, names: dict) -> dict:
    rows = conn.execute(
        """SELECT c.section_key, c.status, c.differences, c.created_at,
                  (SELECT e.document_url FROM divergence_events e WHERE e.section_key = c.section_key AND e.kind = 'explained'
                   ORDER BY e.id DESC LIMIT 1)
           FROM latest_comparisons c WHERE c.section_key LIKE %s AND c.status IN ('divergent', 'conflict')
           ORDER BY c.created_at DESC""", (f"{turn}:%",)).fetchall()
    items = []
    for key, status, diffs, at, explained in rows:
        _, uf, mun, zone, section = key.split(":")
        items.append({"key": key, "uf": uf.upper(), "municipality": names.get((uf, int(mun)), mun), "zone": int(zone), "section": int(section),
                      "status": "explained" if explained else status, "differences": diffs, "since": at.isoformat(), "document": explained})
    return {"turn": turn, "updatedAt": datetime.now(timezone.utc).isoformat(), "items": items}


def publish_local(conn: psycopg.Connection, turn: int, public: Path) -> None:
    totals, names = place_index(public / "places")
    out = public / "aggregates" / str(turn)
    out.mkdir(parents=True, exist_ok=True)
    (out / "coverage.json").write_text(json.dumps(coverage(conn, turn, totals)))
    (out / "divergences.json").write_text(json.dumps(divergences(conn, turn, names), ensure_ascii=False))
