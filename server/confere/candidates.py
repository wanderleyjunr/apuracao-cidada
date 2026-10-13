"""Builds the app candidate indexes from TSE official result payloads (status as declared by the TSE).

Inputs (extracted from resultados.tse.jus.br *-u.jws, Brazil-only): fixtures/tse-official-status-1t.json (President BR)
and fixtures/tse-official-status-1t-states.json (Governor + Senator, every UF).
Outputs:
  results/1/candidates.json — 1st round, every candidate with votes/status.
  results/2/candidates.json — 2nd round line-up: candidates the TSE declared "2º turno" (President + Governors).
Keys: "1" (President, national) and "<office>:<uf>" (e.g. "3:ac", "5:mg").
CLI: uv run python -m confere.candidates <president.json> <states.json> <results_dir>
"""
import json
import sys
from pathlib import Path

OFFICE_NAMES = {"1": "Presidente", "3": "Governador", "5": "Senador", "6": "Deputado Federal", "7": "Deputado Estadual"}
FIELDS = ("n", "name", "party", "sq", "status", "votes", "pct")


def index(sources: list[dict]) -> dict:
    offices: dict = {}
    for src in sources:
        for c in src["candidates"]:
            key = "1" if c["office"] == "1" else f"{c['office']}:{c.get('uf') or c['scope']}"
            offices.setdefault(key, []).append({k: c[k] for k in FIELDS})
    for lst in offices.values():
        lst.sort(key=lambda c: -c["votes"])
    return offices


def build(president: dict, states: dict) -> tuple[dict, dict]:
    president = {**president, "candidates": [c for c in president["candidates"] if c["office"] == "1"]}
    first = index([president, states])
    declared = f"{president['meta'][0]['dg']} {president['meta'][0]['hg']}"
    runoff = {k: [{**c, "votes": 0, "pct": ""} for c in v if c["status"] == "2º turno"] for k, v in first.items()}
    runoff = {k: v for k, v in runoff.items() if v}
    return ({"declaredAt": declared, "names": OFFICE_NAMES, "offices": first},
            {"declaredAt": declared, "names": OFFICE_NAMES, "offices": runoff})


if __name__ == "__main__":
    t1, t2 = build(json.loads(Path(sys.argv[1]).read_text()), json.loads(Path(sys.argv[2]).read_text()))
    for turn, doc in ((1, t1), (2, t2)):
        p = Path(sys.argv[3]) / str(turn) / "candidates.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    print("runoff:", {k: [c["name"] for c in v] for k, v in t2["offices"].items()})
