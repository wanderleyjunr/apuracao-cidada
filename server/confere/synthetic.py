"""Synthetic ballot QR texts for LOCAL TESTS ONLY (valid hash chain, no signature). Never publish these.
CLI: uv run python -m confere.synthetic <uf> <mun> <zone> <section> <votes.json: {office: {number|BRAN|NULO: n}}>
"""
import json
import sys

from .ballot import sha512


def p521_key_and_cert():
    """Throwaway P-521 key + self-signed DER certificate (like an urna 2013/2015). Tests only."""
    from datetime import datetime, timedelta, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP521R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "urna-teste")])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(1).not_valid_before(now).not_valid_after(now + timedelta(days=1)).sign(key, hashes.SHA512()))
    return key, cert.public_bytes(serialization.Encoding.DER)


def make(uf: str, mun: int, zone: int, section: int, votes: dict, turn: int = 1, signer=None) -> list[str]:
    """signer = (key, cert_der) from p521_key_and_cert() adds ASSI + QRCE parts; None = unsigned."""
    head = f"ORIG:VOTA ORLC:LEG PROC:3220 DTPL:2026100{4 if turn == 1 else 0} PLEI:3220 TURN:{turn} FASE:O UNFE:{uf.upper()} MUNI:{mun} ZONA:{zone} SECA:{section} IDUE:9999999 VERS:test HRFC:170200"
    offices = []
    for office, v in votes.items():
        nominal = sum(n for k, n in v.items() if k.isdigit())
        cand = " ".join(f"{k}:{n}" for k, n in v.items() if k.isdigit())
        offices.append(f"CARG:{office} TIPO:0 {cand} NOMI:{nominal} BRAN:{v.get('BRAN', 0)} NULO:{v.get('NULO', 0)} TOTC:{nominal + v.get('BRAN', 0) + v.get('NULO', 0)}")
    data = f"{head} {' '.join(offices)}"
    h = sha512(data)
    if not signer:
        return [f"QRBU:1:1 VRQR:6.0 {data} HASH:{h}"]
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import Prehashed

    key, cert = signer
    sig = key.sign(bytes.fromhex(h), ec.ECDSA(Prehashed(hashes.SHA512()))).hex().upper()
    return [f"QRBU:1:1 VRQR:6.0 {data} HASH:{h} ASSI:{sig}", f"QRCE:1:1 IDUE:9999999 CERT:{cert.hex().upper()}"]


if __name__ == "__main__":
    print(json.dumps(make(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), json.loads(sys.argv[5]))))
