"""Compact place index for the app's cascading selector (UF → municipality → zone → section).

Built from the TSE config cs.json (one per UF) and published as places/<uf>.json on the public CDN.
CLI: uv run python -m confere.places <cs.json> <out.json>
"""
import json
import sys
from pathlib import Path


def build_places(cfg: dict) -> dict:
    """{"uf": "mg", "municipalities": [{"code": 53112, "name": "SENADOR CORTES", "zones": {"170": [33, 34]}}]} sorted by name."""
    state = cfg["abr"][0]
    municipalities = [
        {
            "code": int(mu["cd"]),
            "name": mu["nm"],
            "zones": {str(int(z["cd"])): sorted(int(s["ns"]) for s in z["sec"]) for z in mu["zon"]},
        }
        for mu in state["mu"]
    ]
    return {"uf": state["cd"], "municipalities": sorted(municipalities, key=lambda m: m["name"])}


if __name__ == "__main__":
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_places(json.loads(src.read_text())), ensure_ascii=False, separators=(",", ":")))
