"""Converts the TSE open-data "boletim de urna" CSV (bweb_<turn>t_<UF>_*.zip, cdn.tse.jus.br) into per-zone JSON.

Output: <out>/<turn>/<uf>/<municipality>/<zone>.json =
  {"sections": {"37": {"apt": 280, "comp": 195, "received": "04/10/2026 18:47:10", "urna": "2250280",
                       "votes": {"1": {"13": 109, "22": 63, "BRAN": 2, "NULO": 4}, "3": {...}}}}}
CLI: uv run python -m confere.bweb <bweb.zip> <out_dir> [offices=1,3,5]
These are the TSE's official per-section numbers (the "TSE side" of every comparison).
"""
import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

BLANK_NULL = {"95": "BRAN", "96": "NULO"}  # NR_VOTAVEL for blank / null in bweb
NULL_TYPES = {"2": "BRAN", "3": "NULO"}  # CD_TIPO_VOTAVEL fallback


def rows(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as raw:
            yield from csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";")


def convert(records, offices: set[str]) -> dict:
    """{(turn, uf, municipality, zone): {"sections": {...}}} from bweb rows."""
    out: dict = defaultdict(lambda: {"sections": {}})
    for r in records:
        office = r["CD_CARGO_PERGUNTA"]
        if office not in offices:
            continue
        zone_key = (r["NR_TURNO"], r["SG_UF"].lower(), int(r["CD_MUNICIPIO"]), int(r["NR_ZONA"]))
        sec = out[zone_key]["sections"].setdefault(str(int(r["NR_SECAO"])), {"votes": {}})
        if office == "1" or "apt" not in sec:  # turnout fields repeat per office; President is the reference
            agg = r.get("DS_SECOES_AGREGADAS", "")
            sec.update(apt=int(r["QT_APTOS"]), comp=int(r["QT_COMPARECIMENTO"]), received=r.get("DT_BU_RECEBIDO", ""),
                       urna=r.get("NR_URNA_EFETIVADA", ""), closed=r.get("DT_ENCERRAMENTO", ""),
                       **({"agg": agg} if agg and agg != "#NULO#" else {}))
        key = BLANK_NULL.get(r["NR_VOTAVEL"]) or NULL_TYPES.get(r["CD_TIPO_VOTAVEL"]) or r["NR_VOTAVEL"]
        votes = sec["votes"].setdefault(office, {})
        votes[key] = votes.get(key, 0) + int(r["QT_VOTOS"])
    return out


def city_totals(records, offices: set[str]) -> dict:
    """{(turn, uf, municipality): {office: {number|BRAN|NULO: votes}}} — used for proportional offices (deputies)."""
    out: dict = defaultdict(dict)
    for r in records:
        office = r["CD_CARGO_PERGUNTA"]
        if office not in offices:
            continue
        votes = out[(r["NR_TURNO"], r["SG_UF"].lower(), int(r["CD_MUNICIPIO"]))].setdefault(office, {})
        key = BLANK_NULL.get(r["NR_VOTAVEL"]) or NULL_TYPES.get(r["CD_TIPO_VOTAVEL"]) or r["NR_VOTAVEL"]
        votes[key] = votes.get(key, 0) + int(r["QT_VOTOS"])
    return out


def write_cities(cities: dict, out_dir: Path) -> int:
    for (turn, uf, mun), doc in cities.items():
        p = out_dir / turn / uf / str(mun) / "city.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"offices": doc}, ensure_ascii=False, separators=(",", ":")))
    return len(cities)


def write(zones: dict, out_dir: Path) -> int:
    for (turn, uf, mun, zone), doc in zones.items():
        p = out_dir / turn / uf / str(mun) / f"{zone}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    return len(zones)


if __name__ == "__main__":
    # usage: <zip> <out> [zone offices=1,3,5] [city offices=6,7]
    zone_offices = set((sys.argv[3] if len(sys.argv) > 3 else "1,3,5").split(","))
    city_offices = set((sys.argv[4] if len(sys.argv) > 4 else "6,7").split(","))
    # the zip is streamed twice (zones, then cities) to keep memory flat
    print(write(convert(rows(Path(sys.argv[1])), zone_offices), Path(sys.argv[2])), "zone files")
    print(write_cities(city_totals(rows(Path(sys.argv[1])), city_offices), Path(sys.argv[2])), "city files")
