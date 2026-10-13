from confere.candidates import build

P = {"meta": [{"dg": "05/10/2026", "hg": "12:51:47"}], "candidates": [
    {"office": "1", "uf": "br", "n": "13", "name": "LULA", "party": "PT", "sq": "1", "status": "2º turno", "votes": 10, "pct": "45"},
    {"office": "1", "uf": "br", "n": "55", "name": "X", "party": "PSD", "sq": "2", "status": "Não eleito", "votes": 1, "pct": "2"}]}
S = {"meta": [], "candidates": [
    {"office": "3", "uf": "ac", "n": "11", "name": "A", "party": "P", "sq": "3", "status": "2º turno", "votes": 5, "pct": "40"},
    {"office": "3", "uf": "mg", "n": "10", "name": "B", "party": "R", "sq": "4", "status": "Eleito", "votes": 9, "pct": "55"}]}


def test_runoff_lineup_only_has_declared_second_round_candidates():
    t1, t2 = build(P, S)
    assert set(t1["offices"]) == {"1", "3:ac", "3:mg"}
    assert {k: [c["n"] for c in v] for k, v in t2["offices"].items()} == {"1": ["13"], "3:ac": ["11"]}
    assert t2["offices"]["1"][0]["votes"] == 0
