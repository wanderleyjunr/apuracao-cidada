import json
from pathlib import Path

from confere.places import build_places

CFG = json.loads((Path(__file__).parents[2] / "fixtures/tse-config/mg-p003220-cs.sample.json").read_text())


def test_build_places():
    assert build_places(CFG) == {"uf": "mg", "municipalities": [{"code": 53112, "name": "SENADOR CORTES", "zones": {"170": [36, 37]}}]}
