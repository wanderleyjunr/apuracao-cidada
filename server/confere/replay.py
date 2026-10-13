"""National sum + minute-by-minute replay of the President count, from the TSE bweb CSVs (one zip per UF + ZZ).

extract: <bweb.zip> -> <cache>/<uf>.json = [[uf, mun, zone, section, received, {number|BRAN|NULO: votes}], ...]
build:   <cache dir> <candidates.json> <out dir> -> national.json (sum vs TSE-declared) + replay.json (cumulative per minute,
         ordered by DT_BU_RECEBIDO). Shows how the lead moved as sections arrived; no projection, only TSE numbers.
CLI: uv run python -m confere.replay extract <zip> <cache>   |   uv run python -m confere.replay build <cache> <candidates.json> <out>
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from confere.bweb import BLANK_NULL, NULL_TYPES, rows

PRESIDENT = "1"


def sections(records) -> list[list]:
    by_key: dict = {}
    for r in records:
        if r["CD_CARGO_PERGUNTA"] != PRESIDENT:
            continue
        key = (r["SG_UF"].lower(), int(r["CD_MUNICIPIO"]), int(r["NR_ZONA"]), int(r["NR_SECAO"]))
        sec = by_key.setdefault(key, [*key, r["DT_BU_RECEBIDO"], {}])
        n = BLANK_NULL.get(r["NR_VOTAVEL"]) or NULL_TYPES.get(r["CD_TIPO_VOTAVEL"]) or r["NR_VOTAVEL"]
        sec[5][n] = sec[5].get(n, 0) + int(r["QT_VOTOS"])
    return list(by_key.values())


def build(secs: list[list], declared: list[dict]) -> tuple[dict, dict]:
    total = defaultdict(int)
    for s in secs:
        for n, v in s[5].items():
            total[n] += v
    decl = {c["n"]: c["votes"] for c in declared}
    national = {
        "sections": len(secs),
        "votes": dict(sorted(total.items(), key=lambda kv: -kv[1])),
        "declared": decl,
        "diff": {n: total.get(n, 0) - v for n, v in decl.items()},
        "match": all(total.get(n, 0) == v for n, v in decl.items()),
    }
    timed = sorted((s for s in secs if s[4]), key=lambda s: s[4])
    cum, points, done = defaultdict(int), [], 0
    for i, s in enumerate(timed):
        for n, v in s[5].items():
            cum[n] += v
        done += 1
        minute = s[4][:16]
        if i + 1 == len(timed) or timed[i + 1][4][:16] != minute:  # one point per minute (last section of the minute)
            valid = sum(v for n, v in cum.items() if n not in ("BRAN", "NULO"))
            points.append({"t": minute, "sections": done, "pct": round(done / len(secs) * 100, 2),
                           "valid": valid, "votes": dict(cum)})
    return national, {"sections": len(secs), "untimed": len(secs) - len(timed), "points": points}


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    if cmd == "extract":
        zip_path, cache = Path(args[0]), Path(args[1])
        secs = sections(rows(zip_path))
        cache.mkdir(parents=True, exist_ok=True)
        (cache / f"{secs[0][0]}.json").write_text(json.dumps(secs, separators=(",", ":")))
        print(secs[0][0], len(secs), "sections")
    else:
        cache, cand, out = Path(args[0]), Path(args[1]), Path(args[2])
        secs = [s for f in sorted(cache.glob("*.json")) for s in json.loads(f.read_text())]
        national, replay = build(secs, json.loads(cand.read_text())["offices"][PRESIDENT])
        out.mkdir(parents=True, exist_ok=True)
        (out / "national.json").write_text(json.dumps(national, ensure_ascii=False, indent=1))
        (out / "replay.json").write_text(json.dumps(replay, separators=(",", ":")))
        print(json.dumps({k: national[k] for k in ("sections", "match", "diff")}))
