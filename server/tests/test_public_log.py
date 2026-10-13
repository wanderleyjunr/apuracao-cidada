from confere.public_log import chain, verify

ROWS = [(1, "a" * 128, "1:mg:1:1:1", "2026-10-25T20:01:00Z"), (2, "b" * 128, "1:mg:1:1:2", "2026-10-25T20:02:00Z"),
        (3, "c" * 128, "1:mg:1:1:3", "2026-10-25T20:03:00Z")]


def test_chain_verifies_and_detects_tampering():
    entries = chain(ROWS)
    cp_old = {"count": 2, "head": entries[1][4]}
    cp_new = {"count": 3, "head": entries[2][4]}
    assert verify(entries, cp_old) and verify(entries, cp_new)

    edited = [list(e) for e in entries]
    edited[0][2] = "1:mg:1:1:9"  # someone changes the section of an old entry
    assert not verify(edited, cp_old)
    assert not verify(entries[1:], cp_new)  # someone deletes the first entry
    assert not verify(entries[:2], cp_new)  # entries missing after a checkpoint
