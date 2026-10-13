from pathlib import Path

from confere.bu_dat import decode

BU = Path(__file__).parents[2] / "fixtures/tse-section-mg-53112-0170-0037/o03220mg5311201700037-bu.dat"


def test_president_votes_senador_cortes_section_37():
    president = decode(BU.read_bytes())["1"]
    assert president == {"13": 109, "14": 1, "22": 63, "30": 1, "55": 8, "70": 6, "80": 1, "BRAN": 2, "NULO": 4}
    assert sum(president.values()) == 195
