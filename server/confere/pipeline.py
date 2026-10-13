"""Server pipeline: ingest door ballots and TSE ballots, recompute the section verdict, publish static JSON.

All writes are inserts (schema.sql is append-only). Publishing goes through the edge worker
(PUT /internal/publish/<path>), so this server never needs R2 credentials.
"""
import json
from datetime import datetime, timezone

import httpx
import psycopg
from psycopg.types.json import Jsonb

from . import bu_dat
from .ballot import Ballot, BallotError, assemble, certificate_fingerprint, office_votes, verify_signature_v60
from .compare import verdict

def flat(votes_by_office: dict) -> dict:
    """{office: {key: n}} -> {"office:key": n}: one comparison covers every office (2nd round: President + Governor)."""
    return {f"{o}:{k}": n for o, votes in votes_by_office.items() for k, n in votes.items()}


def signature_status(b: Ballot) -> str:
    """'valid' | 'invalid' | 'unverified' (E-521 library missing, or v1.5 without the TSE key)."""
    if b.version != "6.0":
        return "unverified"
    try:
        return "valid" if verify_signature_v60(b) else "invalid"
    except BallotError:
        return "unverified"
    except Exception:  # malformed certificate etc.
        return "invalid"


def all_votes(b: Ballot) -> dict:
    return {o["CARG"]: office_votes(o) for o in b.offices}


def ingest_submission(conn: psycopg.Connection, msg: dict) -> str:
    """msg = edge SubmissionMessage. Returns the section key to recompute."""
    b = assemble(msg["texts"])  # re-validate: never trust the edge blindly
    known = conn.execute("SELECT 1 FROM ballots WHERE final_hash = %s", (b.final_hash,)).fetchone()
    if not known:  # signature checked once per distinct ballot, not once per witness
        conn.execute(
            """INSERT INTO ballots (final_hash, section_key, version, urna_id, cert_fingerprint, signature_status, origin, fields, votes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (final_hash) DO NOTHING""",
            (b.final_hash, msg["sectionKey"], b.version, b.fields.get("IDUE", ""), certificate_fingerprint(b), signature_status(b),
             b.fields.get("ORIG", ""), Jsonb(b.fields), Jsonb(all_votes(b))),
        )
    conn.execute(
        "INSERT INTO submissions (received_at, final_hash, section_key, raw_key, ip_hash) VALUES (%s, %s, %s, %s, %s)",
        (msg["receivedAt"], b.final_hash, msg["sectionKey"], msg["rawKey"], msg.get("ipHash")),
    )
    return msg["sectionKey"]


def ingest_tse(conn: psycopg.Connection, section_key: str, file_hash: str, received_at: str, bu_bytes: bytes) -> str:
    votes = bu_dat.decode(bu_bytes)
    conn.execute(
        "INSERT INTO tse_ballots (section_key, file_hash, received_at, votes) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        (section_key, file_hash, received_at, Jsonb(votes)),
    )
    return section_key


def recompute(conn: psycopg.Connection, section_key: str) -> dict | None:
    """Inserts a new comparison row if the verdict changed; returns the public section document."""
    door_rows = conn.execute(
        """SELECT b.final_hash, b.votes, b.urna_id, b.signature_status, b.first_seen, count(s.id)
           FROM ballots b JOIN submissions s USING (final_hash)
           WHERE b.section_key = %s AND b.signature_status <> 'invalid'
           GROUP BY b.final_hash ORDER BY b.first_seen""", (section_key,)).fetchall()
    tse_row = conn.execute(
        "SELECT file_hash, received_at, votes FROM tse_ballots WHERE section_key = %s ORDER BY id DESC LIMIT 1", (section_key,)).fetchone()
    tse_votes = tse_row[2] if tse_row else None
    offices = set(tse_votes) if tse_votes else None  # compare only offices the TSE side has
    pick = lambda votes: flat({o: v for o, v in votes.items() if offices is None or o in offices})
    v = verdict([(r[0], pick(r[1])) for r in door_rows], pick(tse_votes) if tse_votes else None)
    if v is None:
        return None
    last = conn.execute("SELECT status, differences FROM latest_comparisons WHERE section_key = %s", (section_key,)).fetchone()
    opened = False
    if not last or (last[0], last[1]) != (v.status, v.differences):
        conn.execute(
            "INSERT INTO comparisons (section_key, status, differences, door_hash, tse_file_hash) VALUES (%s, %s, %s, %s, %s)",
            (section_key, v.status, Jsonb(v.differences), v.door_hash, tse_row[0] if tse_row else None),
        )
        if v.status in ("divergent", "conflict") and (not last or last[0] not in ("divergent", "conflict")):
            conn.execute("INSERT INTO divergence_events (section_key, kind, note) VALUES (%s, 'opened', %s)", (section_key, v.status))
            opened = True
    door = next((r for r in door_rows if r[0] == v.door_hash), None)
    return {
        "key": section_key,
        "status": v.status,
        "differences": v.differences,
        "door": door and {"votes": door[1], "urna": door[2], "signature": door[3],
                          "firstSeen": door[4].isoformat(), "submissions": door[5], "distinctBallots": len(door_rows)},
        "tse": tse_row and {"votes": tse_votes, "receivedAt": tse_row[1], "fileHash": tse_row[0]},
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "opened": opened,  # True only on the transition into divergent/conflict → triggers observer alerts
    }


def section_path(section_key: str) -> str:
    return "sections/" + section_key.replace(":", "/") + ".json"


def publish(edge_url: str, token: str, path: str, doc: dict, client: httpx.Client | None = None) -> None:
    c = client or httpx.Client()
    r = c.put(f"{edge_url}/internal/publish/{path}", content=json.dumps(doc, ensure_ascii=False),
              headers={"authorization": f"Bearer {token}", "content-type": "application/json"}, timeout=15)
    r.raise_for_status()
