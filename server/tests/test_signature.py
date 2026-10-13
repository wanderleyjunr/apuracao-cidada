from confere.ballot import assemble, verify_signature_v60
from confere.pipeline import signature_status
from confere.synthetic import make, p521_key_and_cert

VOTES = {"1": {"13": 10, "22": 9, "BRAN": 1, "NULO": 0}}


def test_v60_p521_signature_end_to_end():
    signer = p521_key_and_cert()
    texts = make("mg", 53112, 170, 37, VOTES, signer=signer)
    b = assemble(texts)
    assert verify_signature_v60(b) and signature_status(b) == "valid"

    other = p521_key_and_cert()  # forger with their own key and certificate signs different votes...
    forged = make("mg", 53112, 170, 37, {"1": {"13": 1, "22": 18, "BRAN": 1, "NULO": 0}}, signer=other)
    assert signature_status(assemble(forged)) == "valid"  # ...self-consistent: why IDUE→certificate consistency matters
    swapped = assemble([forged[0], texts[1]])  # forged votes + the real urna certificate
    assert signature_status(swapped) == "invalid"
