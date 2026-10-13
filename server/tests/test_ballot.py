import json
from pathlib import Path

import pytest

from confere.ballot import BallotError, assemble

FIX = Path(__file__).parents[2] / "fixtures"
BALLOTS_2022 = json.loads((FIX / "ballots-2022-abroad.json").read_text())
BALLOT_2026 = json.loads((FIX / "ballot-2026-manual-simulated.json").read_text())


@pytest.mark.parametrize("texts", BALLOTS_2022)
def test_real_2022_ballots_pass(texts):
    b = assemble(texts)
    assert b.version == "1.5" and b.fields["UNFE"] == "ZZ" and not b.is_official_2026()


def test_2022_votes_nagoya():
    b = next(assemble(t) for t in BALLOTS_2022 if "SECA:265" in t[0])
    assert b.offices[0]["votes"]["22"] == 315 and b.offices[0]["TOTC"] == "415"
    assert b.section_key() == "1:zz:30198:1:265"


def test_2026_manual_example_two_part_chain_any_order():
    b = assemble(list(reversed(BALLOT_2026[0])))
    assert b.version == "6.0" and b.fields["IDUE"] == "2250280"
    assert {o["CARG"] for o in b.offices} == {"6", "7", "5", "3", "1"}
    assert b.signature.startswith("564DD933")


def test_tampered_vote_fails():
    t = next(x[0] for x in BALLOTS_2022 if "SECA:1693" in x[0]).replace(" 13:36 ", " 13:37 ")
    with pytest.raises(BallotError, match="hash inválido"):
        assemble([t])


def test_missing_part_fails():
    with pytest.raises(BallotError, match="Faltam os QR Codes 1 de 2"):
        assemble([BALLOT_2026[0][1]])


def test_tampered_second_part_fails():
    with pytest.raises(BallotError, match="QR Code 2 de 2"):
        assemble([BALLOT_2026[0][0], BALLOT_2026[0][1].replace("93:3", "93:4")])


def test_not_a_ballot():
    with pytest.raises(BallotError, match="não é de um boletim"):
        assemble(["https://exemplo.com"])
