import base64
import json

from confere.run import decode_body


def test_decode_body_json_and_base64():
    m = {"sectionKey": "2:mg:53112:170:37"}
    assert decode_body(json.dumps(m)) == m
    assert decode_body(base64.b64encode(json.dumps(m).encode()).decode()) == m
    assert decode_body(m) == m
