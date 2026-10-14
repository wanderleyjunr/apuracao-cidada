from pathlib import Path

from confere.national import parse


def test_parse_first_round_fixture():
    doc = parse((Path(__file__).parents[2] / "fixtures/tse-national-6257-u.jws").read_text(), 1)
    assert doc["pct"] == 100 and doc["sections"] == {"total": 499248, "counted": 499248}
    top = doc["candidates"][:2]
    assert [(c["n"], c["votes"], c["status"]) for c in top] == [("22", 56104503, "2º turno"), ("13", 53879538, "2º turno")]
    assert doc["votes"]["valid"] == 119300788 and doc["votes"]["blank"] == 2300798
