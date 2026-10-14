"""Build the Apuração Cidadã logo kit (SVG masters + PNG/ICO exports) from code.

    python3 brand/logo/build.py            # needs fonttools + Inter (OFL) and the logo-design skill renderer

Every file in svg/, png/, web/, mobile/ is generated: edit geometry or colours here, never by hand.
"""
import os
import pathlib
import re
import subprocess
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent
FONTS = pathlib.Path(os.environ.get("INTER_DIR", pathlib.Path.home() / "Library/Fonts"))
RENDER = pathlib.Path(os.environ.get("LOGO_SKILL", pathlib.Path.home() / ".claude/skills/logo-design")) / "scripts/render_png.py"

# Palette (matches app DESIGN.md; see README.md)
GREEN = "#0F5257"       # verde-mata: QR corners, "Apuração"
TEAL_DEEP = "#1F8F83"   # turquesa-selo: the check + "Cidadã" on light backgrounds (3.9:1 on white)
TEAL = "#3BB3A6"        # turquesa: the check + "Cidadã" on dark backgrounds (3.5:1 on verde-mata)
INK = "#0D2224"
SURFACE = "#F2F7F6"
WHITE = "#FFFFFF"

SCHEMES = {  # name: (corners/"Apuração", check/"Cidadã")
    "": (GREEN, TEAL_DEEP),
    "-reverse": (WHITE, TEAL),
    "-black": ("#000000", "#000000"),
    "-white": (WHITE, WHITE),
}


def rrect(x0, y0, x1, y1, r):
    return (f"M{x0+r:g} {y0:g}H{x1-r:g}A{r:g} {r:g} 0 0 1 {x1:g} {y0+r:g}V{y1-r:g}A{r:g} {r:g} 0 0 1 {x1-r:g} {y1:g}"
            f"H{x0+r:g}A{r:g} {r:g} 0 0 1 {x0:g} {y1-r:g}V{y0+r:g}A{r:g} {r:g} 0 0 1 {x0+r:g} {y0:g}Z")


def check(cx, cy, s, w):
    """L-shape (long arm 4s, short arm 2s, thickness w) rotated 45deg: a check with its vertex at the bottom."""
    pts = [(2*s, 0), (2*s + w, 0), (2*s + w, 4*s), (0, 4*s), (0, 4*s - w), (2*s, 4*s - w)]
    k = 0.70710678
    pts = [((x - y) * k, (x + y) * k) for x, y in pts]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    dx, dy = cx - (min(xs) + max(xs)) / 2, cy - (min(ys) + max(ys)) / 2
    return "M" + "L".join(f"{x+dx:.1f} {y+dy:.1f}" for x, y in pts) + "Z"


# Symbol on a 256 grid: three QR finders (98 px = 7u, u=14) + the check in the fourth corner, 16 px margin.
U, M = 14, 16
FAR = 256 - M - 7 * U


def finder(x, y, small=False):
    """QR finder, weights evened with the check: ring 20, gap 12, core 34 (7u = 98). Small cut: ring 30, no core."""
    S = 7 * U
    if small:
        return rrect(x, y, x + S, y + S, 28) + rrect(x + 30, y + 30, x + S - 30, y + S - 30, 6)
    return (rrect(x, y, x + S, y + S, 28) + rrect(x + 20, y + 20, x + S - 20, y + S - 20, 12)
            + rrect(x + 32, y + 32, x + S - 32, y + S - 32, 6))


def symbol(c1, c2, small=False):
    corners = finder(M, M, small) + finder(FAR, M, small) + finder(M, FAR, small)
    tick = check(FAR + 3.5*U, FAR + 3.8*U, 22, 30 if small else 22)
    return (f'<path fill="{c1}" fill-rule="evenodd" d="{corners}"/>'
            f'<path fill="{c2}" d="{tick}"/>')


# Wordmark: Inter (SIL OFL) outlined to paths, so no font is needed to display the logo.
_fonts = {}


def font(weight):
    if weight not in _fonts:
        _fonts[weight] = TTFont(FONTS / f"Inter-{weight}.ttf")
    return _fonts[weight]


def text(s, weight, size, x, y, track=-0.02):
    f = font(weight)
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    sc, cx, out = size / upm, x, []
    for ch in s:
        g = gs[cmap[ord(ch)]]
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        g.draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
        out.append(pen.getCommands())
        cx += g.width * sc + track * size
    return "".join(out), cx - x - track * size


def width(s, weight, size):
    return text(s, weight, size, 0, 0)[1]


def cap(weight, size):
    f = font(weight)
    return f["OS/2"].sCapHeight / f["head"].unitsPerEm * size


def svg(w, h, body, title="Apuração Cidadã"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


def words(c1, c2, size, x, base1, base2=None, gap=None, center=None):
    """'Apuração' (Bold, c1) and 'Cidadã' (SemiBold, c2): two lines, or one line when base2 is None."""
    w1, w2 = width("Apuração", "Bold", size), width("Cidadã", "SemiBold", size)
    if base2 is None:
        d1, _ = text("Apuração", "Bold", size, x, base1)
        d2, _ = text("Cidadã", "SemiBold", size, x + w1 + gap, base1)
    else:
        x1 = x2 = x
        if center is not None:
            x1, x2 = center - w1 / 2, center - w2 / 2
        d1, _ = text("Apuração", "Bold", size, x1, base1)
        d2, _ = text("Cidadã", "SemiBold", size, x2, base2)
    return f'<path fill="{c1}" d="{d1}"/><path fill="{c2}" d="{d2}"/>'


def lockups():
    S2 = 112  # two-line size: caps of line 1 align with the symbol top, line 2 sits on its bottom
    tx = 256 + 40
    w2 = tx + max(width("Apuração", "Bold", S2), width("Cidadã", "SemiBold", S2)) + M
    S1 = 128  # one-line size, caps centred on the symbol
    gap1 = 0.28 * S1
    w1 = tx + width("Apuração", "Bold", S1) + gap1 + width("Cidadã", "SemiBold", S1) + M
    sw = max(width("Apuração", "Bold", S2), 256) + 2 * M
    b1 = 256 + 24 + cap("Bold", S2) + 0.12 * S2
    b2 = b1 + 1.12 * S2
    sh = b2 + 24
    out = {}
    for suf, (c1, c2) in SCHEMES.items():
        out[f"symbol{suf}"] = svg(256, 256, symbol(c1, c2))
        out[f"symbol-small{suf}"] = svg(256, 256, symbol(c1, c2, small=True))
        out[f"horizontal{suf}"] = svg(w2, 256, symbol(c1, c2) +
                                      words(c1, c2, S2, tx, M + cap("Bold", S2), 256 - M))
        out[f"inline{suf}"] = svg(w1, 256, symbol(c1, c2) +
                                  words(c1, c2, S1, tx, 128 + cap("Bold", S1) / 2, gap=gap1))
        out[f"stacked{suf}"] = svg(sw, sh, f'<g transform="translate({(sw-256)/2:g} 0)">{symbol(c1, c2)}</g>' +
                                   words(c1, c2, S2, 0, b1, b2, center=sw / 2))
        ww = width("Apuração", "Bold", S1) + gap1 + width("Cidadã", "SemiBold", S1)
        out[f"wordmark{suf}"] = svg(ww, 1.2 * S1, words(c1, c2, S1, 0, S1 * 0.95, gap=gap1))
    return out


def placed(body, canvas, box, bg=None, rx=0):
    """Symbol body (256 grid) scaled to `box` px, centred on a square canvas, optional background."""
    s = box / 256
    o = (canvas - box) / 2
    back = f'<rect width="{canvas}" height="{canvas}" rx="{rx}" fill="{bg}"/>' if bg else ""
    return svg(canvas, canvas, back + f'<g transform="translate({o:g} {o:g}) scale({s:g})">{body}</g>')


def tiles():
    rev = symbol(WHITE, TEAL)
    return {
        # web
        "web/favicon": svg(256, 256, symbol(GREEN, TEAL_DEEP, small=True)),
        "web/icon-tile": placed(rev, 512, 330, GREEN),                 # apple-touch / 192 / 512
        "web/maskable": placed(rev, 512, 280, GREEN),                  # content inside the 80% safe circle
        # mobile (Expo)
        "mobile/icon": placed(rev, 1024, 640, GREEN),                  # iOS: opaque, full bleed, OS rounds it
        "mobile/android-icon-foreground": placed(rev, 1024, 500),      # 66 dp safe zone
        "mobile/android-icon-monochrome": placed(symbol(WHITE, WHITE), 1024, 500),
        "mobile/splash-icon": placed(symbol(GREEN, TEAL_DEEP), 1024, 400),            # shown "contain" full screen
        "mobile/splash-icon-reverse": placed(rev, 1024, 400),
    }


def og_image():
    W, H = 1200, 630
    S2 = 112
    lw = 296 + max(width("Apuração", "Bold", S2), width("Cidadã", "SemiBold", S2))
    x0, y0 = (W - lw) / 2, 150
    body = (f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>'
            f'<g transform="translate({x0:g} {y0})">{symbol(GREEN, TEAL_DEEP)}'
            f'{words(GREEN, TEAL_DEEP, S2, 296, M + cap("Bold", S2), 256 - M)}</g>')
    tag = "O boletim da porta bate com o do TSE?"
    tw = width(tag, "Medium", 40)
    d, _ = text(tag, "Medium", 40, (W - tw) / 2, 500, track=0)
    return svg(W, H, body + f'<path fill="{INK}" fill-opacity=".72" d="{d}"/>')


def render(src, png, **kw):
    args = [sys.executable, str(RENDER), str(src), "-o", str(png)]
    for k, v in kw.items():
        args += [f"--{k}", str(v)]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def main():
    for sub in ("svg", "png", "web", "mobile"):
        (ROOT / sub).mkdir(exist_ok=True)
    files = {f"svg/{k}": v for k, v in lockups().items()} | tiles() | {"web/og-image": og_image()}
    for name, content in files.items():
        (ROOT / f"{name}.svg").write_text(content)
    print(f"wrote {len(files)} SVGs")

    if "--svg-only" in sys.argv:
        return
    # PNG previews / handoff (transparent)
    for n in ("symbol", "symbol-reverse", "symbol-white", "horizontal", "horizontal-reverse", "horizontal-white",
              "inline", "inline-reverse", "stacked", "stacked-reverse", "wordmark"):
        vw, vh = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', files[f"svg/{n}"]).groups())
        render(ROOT / f"svg/{n}.svg", ROOT / f"png/{n}.png", width=round(vw * 4), height=round(vh * 4))
    # web / PWA
    w = ROOT / "web"
    render(w / "favicon.svg", w / "favicon.ico", ico=w / "favicon.ico")
    for px in (16, 32, 48):
        render(w / "favicon.svg", w / f"favicon-{px}.png", size=px)
    render(w / "icon-tile.svg", w / "apple-touch-icon.png", size=180)
    render(w / "icon-tile.svg", w / "icon-192.png", size=192)
    render(w / "icon-tile.svg", w / "icon-512.png", size=512)
    render(w / "maskable.svg", w / "maskable-512.png", size=512)
    render(w / "og-image.svg", w / "og-image.png", width=1200, height=630)
    # mobile (Expo)
    m = ROOT / "mobile"
    for n in ("icon", "android-icon-foreground", "android-icon-monochrome", "splash-icon", "splash-icon-reverse"):
        render(m / f"{n}.svg", m / f"{n}.png", size=1024)
    print("rendered PNG/ICO")


if __name__ == "__main__":
    main()
