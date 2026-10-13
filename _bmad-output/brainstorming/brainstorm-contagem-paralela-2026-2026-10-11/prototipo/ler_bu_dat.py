# ponytail: decodificador heurístico do bu.dat (DER) sem o .asn1 oficial; trocar por asn1tools + bu.asn1 do TSE
import sys
def tlv(b, i):
    t = b[i]; i += 1
    l = b[i]; i += 1
    if l & 0x80:
        n = l & 0x7f; l = int.from_bytes(b[i:i+n], 'big'); i += n
    return t, b[i:i+l], i + l
def kids(b):
    i, out = 0, []
    while i < len(b):
        t, v, i = tlv(b, i); out.append((t, v))
    return out
def walk(b, depth=0, ctx=None):
    for t, v in kids(b):
        if t == 0x30:
            ks = kids(v)
            tags = [k[0] for k in ks]
            if tags[:3] == [0x81, 0x82, 0xA3]:  # votoVotavel: tipo, qtd, identificação
                tipo = int.from_bytes(ks[0][1], 'big'); qtd = int.from_bytes(ks[1][1], 'big')
                ident = [int.from_bytes(x[1], 'big') for x in kids(ks[2][1])]
                print(f"{'  '*depth}tipo={tipo} cod={ident[1]} votos={qtd}")
                continue
            if tags[:3] == [0x81, 0x82, 0x02]:  # branco/nulo
                tipo = int.from_bytes(ks[0][1], 'big'); qtd = int.from_bytes(ks[1][1], 'big')
                print(f"{'  '*depth}tipo={tipo} ({ {2:'nominal?',3:'branco?',4:'nulo?'}.get(tipo,'?') }) votos={qtd}")
                continue
            if tags and tags[0] == 0x81 and len(ks) >= 2 and ks[1][0] == 0x02:
                print(f"{'  '*depth}== cargo {int.from_bytes(ks[0][1],'big')}")
            walk(v, depth + 1)
        elif t == 0x04 and len(v) > 200 and v[0] == 0x30:
            walk(v, depth + 1)
data = open(sys.argv[1], 'rb').read()
walk(data)
