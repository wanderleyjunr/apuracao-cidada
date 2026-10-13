import sys, re, hashlib, zxingcpp
from PIL import Image
RE = re.compile(r"^QRBU:(\d+):(\d+) VRQR:(\S+)(?: VRCH:(\d+))? (.*) HASH:([0-9A-F]{128})(?: ASSI:([0-9A-F]+))?$", re.S)
for p in sys.argv[1:]:
    img = Image.open(p).convert("L")
    rs = zxingcpp.read_barcodes(img) or zxingcpp.read_barcodes(img.resize((img.width*2, img.height*2)))
    for r in rs:
        m = RE.match(r.text.strip())
        d = dict(x.split(":", 1) for x in m[5].split(" "))
        ok = hashlib.sha512(m[5].encode()).hexdigest().upper() == m[6]
        votos = {k: v for k, v in d.items() if k.isdigit()}
        print(f"UF {d['UNFE']} mun {d['MUNI']} zona {d['ZONA']} seção {d['SECA']} urna {d['IDUE']} | votos {votos} brancos {d['BRAN']} nulos {d['NULO']} total {d['TOTC']} | hash OK={ok}")
