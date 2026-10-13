from confere.compare import verdict

TSE = {"13": 112, "22": 95, "BRAN": 3, "NULO": 5}
DOOR = {"13": 112, "22": 98, "BRAN": 3, "NULO": 5}


def test_verdicts():
    assert verdict([], None) is None
    assert verdict([], TSE).status == "tse-only"
    assert verdict([("h1", DOOR)], None).status == "waiting"
    assert verdict([("h1", TSE), ("h1b", TSE)], TSE).status == "identical"  # two senders, same votes
    v = verdict([("h1", DOOR)], TSE)
    assert v.status == "divergent" and v.differences == [{"key": "22", "door": 98, "tse": 95}] and v.door_hash == "h1"


def test_conflicting_door_ballots_never_produce_a_verdict():
    assert verdict([("h1", DOOR), ("h2", TSE)], TSE).status == "conflict"
