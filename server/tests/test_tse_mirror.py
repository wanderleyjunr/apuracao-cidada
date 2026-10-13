import json
from pathlib import Path

from confere.tse_mirror import Section, aux_url, config_url, file_url, latest_files, municipality_names, parse_config

FIX = Path(__file__).parents[2] / "fixtures/tse-config"
CFG = json.loads((FIX / "mg-p003220-cs.sample.json").read_text())
AUX = json.loads((FIX / "p003220-mg-m53112-z0170-s0037-aux.json").read_text())
S37 = Section("mg", 53112, 170, 37, "05/10/2026 00:52:25")


def test_urls_match_real_tse_paths():
    base = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220"
    assert config_url(3220, "mg") == f"{base}/config/mg/mg-p003220-cs.json"
    assert aux_url(3220, S37) == f"{base}/dados/mg/53112/0170/0037/p003220-mg-m53112-z0170-s0037-aux.json"
    assert file_url(3220, S37, "abc", "o03220mg5311201700037-bu.dat") == f"{base}/dados/mg/53112/0170/0037/abc/o03220mg5311201700037-bu.dat"


def test_parse_config():
    assert parse_config(CFG)[1] == S37
    assert S37.key(1) == "1:mg:53112:170:37"
    assert municipality_names(CFG) == {53112: "SENADOR CORTES"}


def test_latest_files():
    h, received, files = latest_files(AUX)
    assert h.startswith("676c39") and received == "04/10/2026 18:47:10"
    assert files["bu"] == "o03220mg5311201700037-bu.dat" and files["vota"].endswith("vota.vsc")
    assert latest_files({"hashes": []}) is None
