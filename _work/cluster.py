#!/usr/bin/env python3
"""
Perceptual clustering of images by similarity, for grouping device photos.
Computes a 64-bit perceptual hash (DCT-based pHash) per image, then greedily
clusters by Hamming distance. Emits:
  - a JSON of clusters -> member filenames
  - a montage of one representative (largest) per cluster, labeled, for manual ID
"""
import os, sys, json, glob
from PIL import Image, ImageDraw, ImageFont
import numpy as np

INDIR = sys.argv[1]
OUT_JSON = sys.argv[2]
OUT_MONTAGE = sys.argv[3]
THRESH = int(sys.argv[4]) if len(sys.argv) > 4 else 10  # hamming dist threshold

def phash(path, size=8, highfreq=4):
    """64-bit DCT pHash. Returns int bit vector as np array of uint8."""
    try:
        im = Image.open(path).convert("L").resize((size * highfreq, size * highfreq), Image.LANCZOS)
    except Exception:
        return None
    a = np.asarray(im, dtype=float)
    # 2D DCT (separable)
    def dct2(x):
        return np.dot(np.dot(dctmtx(x.shape[0]), x), dctmtx(x.shape[1]).T)
    def dctmtx(n):
        # DCT-II matrix
        m = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i == 0:
                    m[i, j] = np.sqrt(1.0 / n)
                else:
                    m[i, j] = np.sqrt(2.0 / n) * np.cos(np.pi * (2 * j + 1) * i / (2 * n))
        return m
    d = dct2(a)
    # top-left size x size low frequencies, drop DC
    d = d[:size, :size]
    med = np.median(d.flatten()[1:])  # exclude DC at [0,0]
    bits = (d > med).astype(np.uint8).flatten()
    return bits

def hamming(a, b):
    return int(np.count_nonzero(a != b))

files = sorted(glob.glob(os.path.join(INDIR, "*.jpg")) + glob.glob(os.path.join(INDIR, "*.jpeg")) + glob.glob(os.path.join(INDIR, "*.png")))
files = [f for f in files if "Screenshot" not in os.path.basename(f)]  # screenshots handled separately

hashes = {}
for f in files:
    h = phash(f)
    if h is not None:
        hashes[f] = h

clusters = []  # list of dict(rep_bits, members=[...])
unassigned = list(hashes.keys())
# process in order; assign to nearest cluster within THRESH
for f in unassigned:
    h = hashes[f]
    best = None
    best_d = 999
    for c in clusters:
        d = hamming(c["rep"], h)
        if d < best_d:
            best_d = d
            best = c
    if best is not None and best_d <= THRESH:
        best["members"].append(f)
    else:
        clusters.append({"rep": h, "members": [f]})

# sort clusters by size desc
clusters.sort(key=lambda c: -len(c["members"]))

# Build output json
out = {}
for i, c in enumerate(clusters):
    members = [os.path.basename(m) for m in c["members"]]
    out[f"cluster_{i+1:02d}"] = {
        "count": len(members),
        "members": members,
    }
with open(OUT_JSON, "w") as f:
    json.dump(out, f, indent=2)

# Montage of largest (by pixel area) representative per cluster
def area(path):
    try:
        with Image.open(path) as im:
            return im.size[0] * im.size[1]
    except Exception:
        return 0

reps = []
for c in clusters:
    rep = max(c["members"], key=area)
    reps.append((f"C{i+1:02d} n={len(c['members'])}", rep))

# Render each rep scaled to fit, in a grid
cols = 4
tw, th = 360, 360
border = 8
n = len(reps)
rows = (n + cols - 1) // cols
cw, ch = tw + border, th + border
W, H = cols * cw + border, rows * ch + border
canvas = Image.new("RGB", (W, H), (235, 235, 235))
d = ImageDraw.Draw(canvas)
from PIL import ImageFont
try:
    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 26)
except Exception:
    font = ImageFont.load_default()
mapping = []
for i, (label, path) in enumerate(reps):
    r, c = divmod(i, cols)
    x = border + c * cw
    y = border + r * ch
    im = Image.open(path).convert("RGB")
    im.thumbnail((tw, th), Image.LANCZOS)
    bg = Image.new("RGB", (tw, th), (255, 255, 255))
    bg.paste(im, ((tw - im.width)//2, (th - im.height)//2))
    canvas.paste(bg, (x, y))
    d.rectangle([x, y, x+tw, y+th], outline=(150,150,150))
    d.text((x+6, y+6), label, fill=(200, 0, 0), font=font)
    mapping.append((label, os.path.basename(path)))
canvas.save(OUT_MONTAGE)
with open(OUT_MONTAGE + ".map.txt", "w") as f:
    for label, p in mapping:
        f.write(f"{label}\t{p}\n")
print(f"Clusters: {len(clusters)}  Images hashed: {len(hashes)}")
for i, c in enumerate(clusters):
    print(f"  C{i+1:02d}: {len(c['members'])} members; rep={os.path.basename(max(c['members'], key=area))}")
