"""Door × TSE comparison for one section (mirror of app/src/state.ts verdict rules).

Votes format: {candidate_number | 'BRAN' | 'NULO': count} for one office (President = '1').
"""
from dataclasses import dataclass, field


@dataclass
class Verdict:
    status: str  # waiting | tse-only | identical | divergent | conflict
    differences: list = field(default_factory=list)  # [{"key", "door", "tse"}]
    door_hash: str | None = None


def differences(door: dict, tse: dict) -> list[dict]:
    keys = sorted(set(door) | set(tse))
    return [{"key": k, "door": door.get(k, 0), "tse": tse.get(k, 0)} for k in keys if door.get(k, 0) != tse.get(k, 0)]


def verdict(door_ballots: list[tuple[str, dict]], tse_votes: dict | None) -> Verdict | None:
    """door_ballots: [(final_hash, votes)] with VALID or unverified signature only. None = nothing to say yet.

    Different door ballots with different votes for the same section = 'conflict' (high-priority alert, no verdict):
    it may be a contingency urna, or a forged ballot that slipped through.
    """
    distinct = {}
    for h, votes in door_ballots:
        distinct.setdefault(tuple(sorted(votes.items())), h)
    if len(distinct) > 1:
        return Verdict("conflict")
    door = next(iter(distinct.items()), None)
    if door and tse_votes is None:
        return Verdict("waiting", door_hash=door[1])
    if not door:
        return Verdict("tse-only") if tse_votes is not None else None
    diff = differences(dict(door[0]), tse_votes)
    return Verdict("divergent" if diff else "identical", diff, door[1])
