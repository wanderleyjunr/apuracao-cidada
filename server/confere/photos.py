"""Official TSE candidate photos (foto_cand2026_<UF>_div.zip, unzipped) -> 96 px square WebP named <sqcand>.webp.
CLI: uv run --with pillow python -m confere.photos <unzipped_dir> <out_dir>
"""
import glob, os, re, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image
SRC, OUT = sys.argv[1], sys.argv[2]

def conv(f):
    m = re.search(r'F[A-Z]{2}(\d+)_div\.jpe?g$', f, re.I)
    if not m: return 0
    dst = f'{OUT}/{m[1]}.webp'
    if os.path.exists(dst): return 0
    try:
        im = Image.open(f).convert('RGB'); w, h = im.size; s = min(w, h); top = 0 if h > w else (h - s) // 2
        im.crop(((w - s) // 2, top, (w - s) // 2 + s, top + s)).resize((96, 96), Image.LANCZOS).save(dst, 'WEBP', quality=72, method=6)
        return 1
    except Exception:
        return 0

if __name__ == '__main__':
    fs = glob.glob(f'{SRC}/**/*.jp*g', recursive=True)
    with ProcessPoolExecutor() as ex: print(sum(ex.map(conv, fs, chunksize=200)), 'new photos of', len(fs))
