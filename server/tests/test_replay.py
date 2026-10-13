from confere.replay import build, sections


def row(sec, n, v, t, office="1"):
    return {"CD_CARGO_PERGUNTA": office, "SG_UF": "MG", "CD_MUNICIPIO": "1", "NR_ZONA": "2", "NR_SECAO": sec,
            "DT_BU_RECEBIDO": t, "NR_VOTAVEL": n, "CD_TIPO_VOTAVEL": "1", "QT_VOTOS": str(v)}


def test_sum_and_replay():
    recs = [row("1", "22", 10, "2026-10-04 18:00:05"), row("1", "13", 5, "2026-10-04 18:00:05"),
            row("2", "13", 20, "2026-10-04 19:30:00"), row("2", "95", 1, "2026-10-04 19:30:00"),
            row("2", "13", 99, "2026-10-04 19:30:00", office="3")]
    national, replay = build(sections(recs), [{"n": "22", "votes": 10}, {"n": "13", "votes": 25}])
    assert national["match"] and national["votes"] == {"13": 25, "22": 10, "BRAN": 1}
    assert [p["t"] for p in replay["points"]] == ["2026-10-04 18:00", "2026-10-04 19:30"]
    assert replay["points"][0]["votes"] == {"22": 10, "13": 5} and replay["points"][1]["valid"] == 35
    assert not build(sections(recs), [{"n": "13", "votes": 24}])[0]["match"]
