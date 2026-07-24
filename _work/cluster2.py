#!/usr/bin/env python3
# Perceptual clustering via HSV color histogram (rotation/lighting stable),
# plus pHash dedup for near-identical shots.
import os, sys, json, glob
from PIL import Image, ImageDraw, ImageFont
import numpy as np

INDIR = sys.argv[1]
OUT_JSON = sys.argv[2]
OUT_MONTAGE = sys.argv[3]
COS_T = float(sys.argv[4]) if len(sys.argv) > 4 else 0.90   # color sim threshold
DEDUP = int(sys.argv[5]) if len(sys.argv) > 5 else 5         # pHash hamming for dup

def phash(path, size=8, hf=4):
    try:
        im = Image.open(path).convert("L").resize((size*hf, size*hf), Image.LANCZOS)
    except Exception:
        return None
    a = np.asarray(im, dtype=float)
    n = size*hf
    def dctmtx(n):
        m = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                c = np.sqrt(1.0/n) if i == 0 else np.sqrt(2.0/n)*np.cos(np.pi*(2*j+1)*i/(2*n))
                m[i, j] = c
        return m
    M = dctmtx(n)
    d = M.dot(a).dot(M.T)[:size, :size]
    med = np.median(d.flatten()[1:])
    return (d > med).astype(np.uint8).flatten()

def hsv_hist(path, bins=(10, 10, 10)):
    try:
        im = Image.open(path).convert("RGB").resize((128, 128))
    except Exception:
        return None
    a = np.asarray(im, dtype=float) / 255.0
    # RGB->HSV (guard against div-by-zero -> NaN)
    with np.errstate(divide="ignore", invalid="ignore"):
        r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
        mx = np.maximum(np.maximum(r,g), b); mn = np.minimum(np.minimum(r,g), b)
        d = mx - mn
        h = np.zeros_like(mx)
        nz = d > 1e-6
        cond = np.zeros_like(mx)
        cond[(mx==r)&(d>0)] = ((g-b)/d)[(mx==r)&(d>0)]
        cond[(mx==g)&(d>0)] = (2.0 + (b-r)/d)[(mx==g)&(d>0)]
        cond[(mx==b)&(d>0)] = (4.0 + (r-g)/d)[(mx==b)&(d>0)]
        h[nz] = (cond[nz] % 6) / 6.0
        h[~nz] = 0.0
        s = np.where(mx > 1e-6, d/mx, 0.0)
        v = mx
    h = np.nan_to_num(h, nan=0.0)
    s = np.nan_to_num(s, nan=0.0)
    H, _ = np.histogramdd(np.stack([h.ravel(), s.ravel(), v.ravel()], axis=1),
                          bins=bins, range=((0,1),(0,1),(0,1)))
    H = H.astype(float).flatten()
    s = H.sum()
    if s > 0:
        H /= s
    return H

def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na*nb))

files = sorted(glob.glob(os.path.join(INDIR, "*.jpg")) +
               glob.glob(os.path.join(INDIR, "*.jpeg")) +
               glob.glob(os.path.join(INDIR, "*.png")))
files = [f for f in files if "Screenshot" not in os.path.basename(f)]

feats = {}
for f in files:
    h = hsv_hist(f)
    if h is not None:
        feats[f] = h

# dedup by pHash
phs = {f: phash(f) for f in feats}
keep = []
dup_of = {}
for f in feats:
    merged = False
    for k in keep:
        if phs[k] is not None and phs[f] is not None and int(np.count_nonzero(phs[k] != phs[f])) <= DEDUP:
            dup_of[f] = k
            merged = True
            break
    if not merged:
        keep.append(f)

clusters = []  # each: dict(rep_feature, members=[])
for f in keep:
    h = feats[f]
    best, bd = None, -1
    for c in clusters:
        s = cos(c["feat"], h)
        if s > bd:
            bd, best = s, c
    if best is not None and bd >= COS_T:
        best["members"].append(f)
    else:
        clusters.append({"feat": h, "members": [f]})

# attach dups to their canonical cluster
for f, k in dup_of.items():
    for c in clusters:
        if c["members"] and c["members"][0] == k:
            c["members"].append(f)
            break

clusters.sort(key=lambda c: -len(c["members"]))
out = {}
for i, c in enumerate(clusters):
    out[f"cluster_{i+1:02d}"] = {"count": len(c["members"]),
                                 "members": [os.path.basename(m) for m in c["members"]]}
with open(OUT_JSON, "w") as fp:
    json.dump(out, fp, indent=2)

def area(p):
    try:
        with Image.open(p) as im:
            return im.size[0]*im.size[1]
    except Exception:
        return 0

cols, tw, th, border = 5, 300, 300, 8
n = len(clusters)
rows = (n + cols - 1)//cols
cw, ch = tw+border, th+border
canvas = Image.new("RGB", (cols*cw+border, rows*ch+border), (235,235,235))
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 22)
except Exception:
    font = ImageFont.load_default()
rep_paths = []
for i, c in enumerate(clusters):
    rep = max(c["members"], key=area)
    rep_paths.append((f"C{i+1:02d} n={len(c['members'])}", rep))
    r, col = divmod(i, cols)
    x, y = border+col*cw, border+r*ch
    im = Image.open(rep).convert("RGB"); im.thumbnail((tw, th), Image.LANCZOS)
    bg = Image.new("RGB", (tw, th), (255,255,255))
    bg.paste(im, ((tw-im.width)//2, (th-im.height)//2))
    canvas.paste(bg, (x, y))
    d.rectangle([x, y, x+tw, y+th], outline=(150,150,150))
    d.text((x+6, y+6), f"C{i+1:02d} n={len(c['members'])}", fill=(200,0,0), font=font)
canvas.save(OUT_MONTAGE)
with open(OUT_MONTAGE + ".map.txt", "w") as fp:
    for lbl, p in rep_paths:
        fp.write(f"{lbl}\t{os.path.basename(p)}\n")
print(f"Clusters={len(clusters)} singletons={sum(1 for c in clusters if len(c['members'])==1)} dups={len(dup_of)}")
for i, c in enumerate(clusters[:40]):
    print(f"  C{i+1:02d}: {len(c['members'])}")
