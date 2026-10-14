"""National President (and state Governor) results exactly as the TSE publishes them (resultados.tse.jus.br, signed JWS).

The TSE rewrites br-c0001-e<election>-u.jws during the count; we mirror it every NATIONAL_INTERVAL_S and publish
results/<turn>/national.json for the apps (default screen). No projection: numbers and status ("Eleito", "2º turno")
are copied from the TSE payload. Election codes from /oficial/comum/config/ele-c.json (6257 = 1st round, 6258 = 2nd).
Governor: <uf>-c0003-e<ele>-u.jws → results/<turn>/<uf>/governor.json, for the UFs the TSE config lists for that turn.
CLI: uv run python -m confere.national <turn> <results_dir>   (President + every Governor race of the turn)
"""
import base64
import json
import sys
from pathlib import Path

import httpx

from .tse_mirror import UFS

import re

BASE = "https://resultados.tse.jus.br/oficial"
ELECTION = {(1, "1"): 6257, (2, "1"): 6258, (1, "3"): 6259, (2, "3"): 6260}  # (turn, office) → TSE election code
UA = {"user-agent": "apuracao-cidada-mirror (open source citizen audit)"}


def url(turn: int, office: str = "1", uf: str = "br") -> str:
    e = ELECTION[(turn, office)]
    return f"{BASE}/ele2026/{e}/dados/{uf}/{uf}-c{int(office):04d}-e{e:06d}-u.jws"


def governor_ufs(turn: int, client: httpx.Client) -> list[str]:
    """UFs with a Governor race in this turn, as listed in the TSE config (2nd round: only the runoffs)."""
    raw = client.get(f"{BASE}/comum/config/ele-c.json", headers=UA).text
    cfg = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))  # the TSE file has trailing commas
    code = str(ELECTION[(turn, "3")])
    ufs = sorted({a["cd"] for pl in cfg["pl"] for e in pl["e"] if e["cd"] == code for a in e.get("abr", []) if a["cd"] != "br"})
    return ufs or [u for u in UFS if u != "zz"]  # 1st round is listed as "br": every state elects a governor


def parse(jws: str, turn: int, office: str = "1", uf: str = "br") -> dict:
    payload = jws.strip().split(".")[1]
    p = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    num = lambda x: float(str(x).replace(",", ".")) if x not in (None, "") else 0.0  # noqa: E731
    cands = [
        {"n": c["n"], "sq": c["sqcand"], "name": c["nmu"], "party": par["sg"], "votes": int(c["vap"] or 0),
         "pct": num(c.get("pvapn")), "status": c.get("st", "")}
        for agr in p["carg"][0]["agr"] for par in agr["par"] for c in par["cand"]
    ]
    s, v = p["s"], p["v"]
    return {
        "turn": turn, "election": p["ele"], "updatedAt": f"{p['dg']} {p['hg']}",
        "pct": num(s["pstn"]), "sections": {"total": int(s["ts"]), "counted": int(s["st"])},
        "votes": {"valid": int(v["vv"]), "blank": int(v["vb"]), "null": int(v["tvn"])},
        "candidates": sorted(cands, key=lambda c: (-c["votes"], int(c["n"]))),
        "source": url(turn, office, uf),
    }


def fetch(turn: int, client: httpx.Client, office: str = "1", uf: str = "br") -> dict:
    r = client.get(url(turn, office, uf), headers=UA)
    r.raise_for_status()
    return parse(r.text, turn, office, uf)


def fetch_all(turn: int, client: httpx.Client) -> dict[str, dict]:
    """{public path: doc} for President + every Governor race the TSE lists for this turn."""
    docs = {f"results/{turn}/national.json": fetch(turn, client)}
    for uf in governor_ufs(turn, client):
        docs[f"results/{turn}/{uf}/governor.json"] = fetch(turn, client, "3", uf)
    return docs


if __name__ == "__main__":
    turn, out = int(sys.argv[1]), Path(sys.argv[2])
    with httpx.Client(timeout=30) as client:
        docs = fetch_all(turn, client)
    for path, doc in docs.items():
        p = out / path.removeprefix("results/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
        print(path, doc["updatedAt"], doc["pct"], [(c["n"], c["votes"]) for c in doc["candidates"][:2]])
