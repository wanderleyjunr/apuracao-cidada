"""Per-candidate JSON pages from TSE open data (consulta_cand_2026.zip + bem_candidato_2026.zip).

Output: <out>/candidates/<sq>.json — one small file per candidate, loaded only when the user opens the page.
LGPD/data minimization: CPF, voter ID (título), e-mail and social name are NEVER copied.
CLI: uv run python -m confere.candidate_pages <consulta_cand.zip> <bem_candidato.zip> <out_dir>
"""
import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

PUBLIC_FIELDS = {  # source column -> output key (allow-list: anything else is dropped)
    "NM_CANDIDATO": "fullName", "NM_URNA_CANDIDATO": "name", "NR_CANDIDATO": "number", "DS_CARGO": "office",
    "CD_CARGO": "officeCode", "SG_UF": "uf", "NM_UE": "scope", "SG_PARTIDO": "party", "NM_PARTIDO": "partyName",
    "NM_FEDERACAO": "federation", "NM_COLIGACAO": "coalition", "DS_COMPOSICAO_COLIGACAO": "coalitionParties",
    "SG_UF_NASCIMENTO": "birthUf", "DS_GENERO": "gender", "DS_GRAU_INSTRUCAO": "education", "DS_COR_RACA": "race",
    "DS_OCUPACAO": "occupation", "DS_SITUACAO_CANDIDATURA": "candidacyStatus", "DS_SIT_TOT_TURNO": "result",
    "NR_TURNO": "round",
}
NULLS = {"#NULO", "#NULO#", "#NE", "-1", ""}


def _csv_rows(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.lower().endswith(".csv") and not name.upper().endswith("_BRASIL.CSV"):
                with z.open(name) as raw:
                    yield from csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";")


def age_on(birth: str, when: date = date(2026, 10, 4)) -> int | None:
    try:
        d, m, y = map(int, birth.split("/"))
    except ValueError:
        return None
    return when.year - y - ((when.month, when.day) < (m, d))


def candidate_doc(row: dict) -> dict:
    doc = {out: row[src] for src, out in PUBLIC_FIELDS.items() if row.get(src, "") not in NULLS}
    doc["sq"] = row["SQ_CANDIDATO"]
    doc["age"] = age_on(row.get("DT_NASCIMENTO", ""))
    return doc


def assets_by_candidate(rows) -> dict:
    out = defaultdict(lambda: {"total": 0.0, "items": []})
    for r in rows:
        value = float(r.get("VR_BEM_CANDIDATO", "0").replace(",", ".") or 0)
        a = out[r["SQ_CANDIDATO"]]
        a["total"] += value
        a["items"].append({"type": r.get("DS_TIPO_BEM_CANDIDATO", ""), "value": value})
    for a in out.values():
        a["items"].sort(key=lambda i: -i["value"])
        a["items"] = a["items"][:20]  # descriptions are free text: keep only type + value, top 20
        a["total"] = round(a["total"], 2)
    return out


def build(cand_zip: Path, assets_zip: Path, out_dir: Path) -> int:
    assets = assets_by_candidate(_csv_rows(assets_zip))
    docs: dict[str, dict] = {}
    for row in _csv_rows(cand_zip):
        doc = candidate_doc(row)
        prev = docs.get(doc["sq"])
        if prev is None or int(doc.get("round", 1)) > int(prev.get("round", 1)):  # keep the latest round's result
            docs[doc["sq"]] = doc
    write_deputies_index(docs.values(), out_dir)
    target = out_dir / "candidates"
    target.mkdir(parents=True, exist_ok=True)
    for sq, doc in docs.items():
        if sq in assets:
            doc["assets"] = assets[sq]
        (target / f"{sq}.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    return len(docs)


def write_deputies_index(docs, out_dir: Path) -> None:
    """results/1/<uf>/deputies.json: {"6"|"7": {number: [sq, name, party, result]}} — names for city totals."""
    by_uf: dict = defaultdict(lambda: {"6": {}, "7": {}})
    for d in docs:
        if d.get("officeCode") in ("6", "7") and "number" in d:
            by_uf[d["uf"].lower()][d["officeCode"]][d["number"]] = [d["sq"], d.get("name", ""), d.get("party", ""), d.get("result", "")]
    for uf, idx in by_uf.items():
        p = out_dir / "results" / "1" / uf / "deputies.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    print(build(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])), "candidate pages")
