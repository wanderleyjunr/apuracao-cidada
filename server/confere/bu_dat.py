"""Decoder for the TSE per-section `bu.dat` (ASN.1 DER) published at resultados.tse.jus.br.

ponytail: heuristic DER walk — the official 2022 bu.asn1 only decodes the 2026 envelope. Replace with
asn1tools + the 2026 spec once the TSE answers (email 2026-10-11). Validated on fixtures/tse-section-mg-53112-0170-0037.
Vote tuple: SEQUENCE{ [1] type, [2] count, [3]{ party, code, ... }, OCTET STRING signature64 }.
Types: 1 nominal, 2 blank (BRAN), 3 null (NULO), 4 party/legenda. Office ids: 1 = President.
"""
VOTE_TYPES = {1: "nominal", 2: "BRAN", 3: "NULO", 4: "party"}


def _tlv(b: bytes, i: int):
    tag = b[i]
    length = b[i + 1]
    i += 2
    if length & 0x80:
        n = length & 0x7F
        length = int.from_bytes(b[i:i + n], "big")
        i += n
    return tag, b[i:i + length], i + length


def _children(b: bytes):
    i, out = 0, []
    while i < len(b):
        tag, value, i = _tlv(b, i)
        out.append((tag, value))
    return out


def _int(v: bytes) -> int:
    return int.from_bytes(v, "big")


def decode(data: bytes) -> dict[str, dict[str, int]]:
    """Returns {office_id: {candidate_number | 'BRAN' | 'NULO' | 'P<party>': count}}."""
    offices: dict[str, dict[str, int]] = {}

    def walk(b: bytes, office: str | None):
        for tag, value in _children(b):
            if tag == 0x30:
                kids = _children(value)
                tags = [k[0] for k in kids]
                if tags[:3] == [0x81, 0x82, 0xA3]:  # vote for an identified votável
                    vtype, count = _int(kids[0][1]), _int(kids[1][1])
                    ident = [_int(x[1]) for x in _children(kids[2][1])]
                    key = str(ident[1]) if vtype == 1 else f"P{ident[1]}"
                    offices.setdefault(office or "?", {})[key] = count
                    continue
                if tags[:2] == [0x81, 0x82] and (len(tags) < 3 or tags[2] != 0xA3):  # blank/null
                    vtype, count = _int(kids[0][1]), _int(kids[1][1])
                    if VOTE_TYPES.get(vtype) in ("BRAN", "NULO"):
                        offices.setdefault(office or "?", {})[VOTE_TYPES[vtype]] = count
                    continue
                if tags and tags[0] == 0x81 and len(kids) >= 2 and kids[1][0] == 0x02:  # office header
                    walk(value, str(_int(kids[0][1])))
                    continue
                walk(value, office)
            elif tag == 0x04 and len(value) > 200 and value[0] == 0x30:  # nested envelope content
                walk(value, office)

    walk(data, None)
    return offices
