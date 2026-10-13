"""Ballot (Boletim de Urna) QR Code parsing and validation — formats 1.5 and 6.0.

Spec: TSE manual "QRCODE no Boletim de Urna" 2026, sections 1.4–1.6 (fixtures/ and _bmad-output/.../tse/).
Mirror of shared/ballot.ts: both must pass the same fixtures. User-facing messages stay in Portuguese.
"""
import hashlib
import re
from dataclasses import dataclass, field

QRBU_RE = re.compile(
    r"^QRBU:(\d+):(\d+) VRQR:(\S+)(?: VRCH:(\d+))? (.*?) HASH:([0-9A-F]{128})(?: ASSI:([0-9A-F]+))?$", re.S
)
QRCE_RE = re.compile(r"^QRCE:(\d+):(\d+) (.*)$", re.S)
VERSIONS = {"1.5", "6.0"}
# OIDs of the urna certificate public key
OID_ECDSA = "1.2.840.10045.2.1"  # P-521, urnas 2013/2015
OID_ED521 = "1.3.6.1.4.1.44588.2.1"  # E-521, urnas 2020/2022


class BallotError(ValueError):
    """Validation error; the message is Portuguese and safe to show to the sender."""


@dataclass
class Part:
    index: int
    total: int
    version: str
    data: str
    hash: str
    signature: str | None = None


@dataclass
class Ballot:
    version: str
    fields: dict  # header/identification: UNFE, MUNI, ZONA, SECA, IDUE, ORIG, TURN, FASE, DTPL...
    offices: list = field(default_factory=list)  # [{"CARG": "1", "votes": {"13": 109}, "BRAN": "2", ...}]
    final_hash: str = ""
    signature: str | None = None
    certificate: bytes | None = None
    texts: list = field(default_factory=list)

    def section_key(self) -> str:
        f = self.fields
        return f"{f['TURN']}:{f['UNFE'].lower()}:{int(f['MUNI'])}:{int(f['ZONA'])}:{int(f['SECA'])}"

    def is_official_2026(self) -> bool:
        return self.fields.get("FASE") == "O" and self.fields.get("DTPL", "").startswith("2026")


def sha512(text: str) -> str:
    return hashlib.sha512(text.encode("ascii")).hexdigest().upper()


def parse_part(text: str) -> Part:
    m = QRBU_RE.match(text.strip())
    if not m:
        raise BallotError("Este QR Code não é de um boletim de urna ou está incompleto. Leia de novo.")
    if m[3] not in VERSIONS:
        raise BallotError(f"Formato de QR Code não suportado (versão {m[3]}).")
    return Part(int(m[1]), int(m[2]), m[3], m[5], m[6], m[7])


def check_chain(parts: list[Part]) -> str:
    """hash1 = SHA-512(data1); hashN = SHA-512(data1 HASH:h1 ... dataN). Returns the signed (final) hash."""
    acc = ""
    for p in parts:
        payload = p.data if not acc else f"{acc} {p.data}"
        if sha512(payload) != p.hash:
            raise BallotError(f"O QR Code {p.index} de {p.total} não confere (hash inválido). O boletim pode ter sido alterado.")
        acc = f"{payload} HASH:{p.hash}"
    return parts[-1].hash


def _records(data: str):
    for rec in data.split(" "):
        key, _, value = rec.partition(":")
        yield key, value


def interpret(data: str) -> tuple[dict, list]:
    """Splits general fields from per-office votes. Pure-number keys are candidates/parties."""
    fields, offices, current = {}, [], None
    for key, value in _records(data):
        if key == "CARG":
            current = {"CARG": value, "votes": {}}
            offices.append(current)
        elif current is None:
            fields[key] = value
        elif key.isdigit():
            current["votes"][key] = current["votes"].get(key, 0) + int(value)
        else:
            current[key] = value  # TIPO, NOMI, BRAN, NULO, TOTC, LEGC, PART...
    return fields, offices


def check_sums(offices: list) -> None:
    for o in offices:
        if "TOTC" not in o:
            continue
        total = sum(int(o.get(k, 0)) for k in ("NOMI", "LEGC", "BRAN", "NULO"))
        if total != int(o["TOTC"]):
            raise BallotError(f"Cargo {o['CARG']}: a soma dos votos ({total}) não bate com o total apurado ({o['TOTC']}).")


def assemble(texts: list[str]) -> Ballot:
    """Takes every QR text (any order, duplicates ignored); validates sequence, hash chain and sums."""
    parts, certs = {}, {}
    unique = list(dict.fromkeys(t.strip() for t in texts))
    for t in unique:
        if t.startswith("QRCE:"):
            m = QRCE_RE.match(t)
            certs[int(m[1])] = (int(m[2]), dict(_records(m[3])))
            continue
        p = parse_part(t)
        parts[p.index] = p
    if not parts:
        raise BallotError("Nenhum QR Code de boletim encontrado.")
    total = next(iter(parts.values())).total
    missing = [i for i in range(1, total + 1) if i not in parts]
    if missing:
        raise BallotError(f"Faltam os QR Codes {', '.join(map(str, missing))} de {total}. Leia todos os do boletim.")
    ordered = [parts[i] for i in range(1, total + 1)]
    final_hash = check_chain(ordered)
    fields, offices = interpret(" ".join(p.data for p in ordered))
    check_sums(offices)
    cert = None
    if certs:
        n = next(iter(certs.values()))[0]
        if sorted(certs) != list(range(1, n + 1)):
            raise BallotError("Faltam QR Codes do certificado da urna (QRCE) no fim do boletim.")
        cert = bytes.fromhex("".join(certs[i][1].get("CERT", "") for i in range(1, n + 1)))
    return Ballot(ordered[0].version, fields, offices, final_hash, ordered[-1].signature, cert, unique)


def office_votes(office: dict) -> dict:
    """Votes of one office in comparison format: candidate number | 'BRAN' | 'NULO' -> count."""
    return {**office["votes"], "BRAN": int(office.get("BRAN", 0)), "NULO": int(office.get("NULO", 0))}


# ---------- signatures ----------

def verify_signature_v15(ballot: Ballot, ed25519_public_key: bytes) -> bool:
    """Format 1.5: Ed25519 over the final hash bytes, with the TSE per-UF public key."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        Ed25519PublicKey.from_public_bytes(ed25519_public_key).verify(
            bytes.fromhex(ballot.signature), bytes.fromhex(ballot.final_hash)
        )
        return True
    except InvalidSignature:
        return False


def _certificate_der(cert: bytes) -> bytes:
    if cert.startswith(b"-----BEGIN"):  # urnas 2020/2022: PEM
        from asn1crypto import pem

        return pem.unarmor(cert)[2]
    return cert  # urnas 2013/2015: DER


def certificate_fingerprint(ballot: Ballot) -> str | None:
    """SHA-256 of the urna certificate: used to check IDUE→certificate consistency across submissions."""
    return hashlib.sha256(_certificate_der(ballot.certificate)).hexdigest() if ballot.certificate else None


def verify_signature_v60(ballot: Ballot) -> bool:
    """Format 6.0: signature with the key from the certificate printed on the ballot (QRCE).

    ponytail: follows the 2026 manual example (ecpy); NOT tested with a real 2026 ballot yet.
    Does NOT validate the certificate chain up to the TSE CA (the manual does not document the root).
    """
    if not ballot.certificate or not ballot.signature:
        raise BallotError("Boletim sem certificado (QRCE) ou sem assinatura: leia também os QR Codes do final.")
    from asn1crypto import x509
    from ecpy.curves import Curve
    from ecpy.ecdsa import ECDSA
    from ecpy.eddsa import EDDSA
    from ecpy.keys import ECPublicKey

    cert = x509.Certificate.load(_certificate_der(ballot.certificate))
    spki = cert["tbs_certificate"]["subject_public_key_info"]
    oid = spki["algorithm"]["algorithm"].dotted
    key = spki["public_key"].contents[1:]  # BIT STRING without the unused-bits byte
    msg, sig = bytes.fromhex(ballot.final_hash), bytes.fromhex(ballot.signature)
    if oid == OID_ECDSA:  # OpenSSL via `cryptography`: 0.37 ms vs 54 ms with pure-Python ecpy (loadtest.py)
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.asymmetric.utils import Prehashed

        pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP521R1(), key)
        try:
            pub.verify(sig, msg, ec.ECDSA(Prehashed(hashes.SHA512())))  # signs the 64-byte SHA-512 hashN as-is
            return True
        except InvalidSignature:
            return False
    if oid == OID_ED521:
        curve = Curve.get_curve("Ed521")
        if curve is None:  # public ecpy 1.2.5 has no E-521; the manual cites "a library provided by the TSE"
            raise BallotError("Verificação E-521 indisponível: falta a curva Ed521 no ecpy (pedida ao TSE).")
        return EDDSA(hashlib.shake_256, hash_len=132).verify(msg, sig, ECPublicKey(curve.decode_point(key)))
    raise BallotError(f"Algoritmo de assinatura não suportado: {oid}")
