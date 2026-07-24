#!/usr/bin/env python3
# Chunk image dir into labeled grids of N per grid (sequential global index).
import os, sys, json, glob
from PIL import Image, ImageDraw, ImageFont

INDIR = sys.argv[1]; OUTDIR = sys.argv[2]
PER = int(sys.argv[3]) if len(sys.argv) > 3 else 24
COLS = int(sys.argv[4]) if len(sys.argv) > 4 else 6
TW = TH = int(sys.argv[5]) if len(sys.argv) > 5 else 340
BORDER = 8

files = sorted(glob.glob(os.path.join(INDIR, "*.jpg")) +
               glob.glob(os.path.join(INDIR, "*.jpeg")) +
               glob.glob(os.path.join(INDIR, "*.png")))
files = [f for f in files if "Screenshot" not in os.path.basename(f)]

try:
    font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 22)
except Exception:
    font = ImageFont.load_default()

os.makedirs(OUTDIR, exist_ok=True)
global_map = []
grids = (len(files) + PER - 1) // PER
for g in range(grids):
    chunk = files[g*PER:(g+1)*PER]
    rows = (len(chunk) + COLS - 1)//COLS
    cw, ch = TW+BORDER, TH+BORDER
    canvas = Image.new("RGB", (COLS*cw+BORDER, rows*ch+BORDER), (235,235,235))
    d = ImageDraw.Draw(canvas)
    for i, f in enumerate(chunk):
        gi = g*PER + i + 1  # global 1-based index
        r, c = divmod(i, COLS)
        x, y = BORDER+c*cw, BORDER+r*ch
        im = Image.open(f).convert("RGB"); im.thumbnail((TW, TH), Image.LANCZOS)
        bg = Image.new("RGB", (TW, TH), (255,255,255))
        bg.paste(im, ((TW-im.width)//2, (TH-im.height)//2))
        canvas.paste(bg, (x, y))
        d.rectangle([x, y, x+TW, y+TH], outline=(150,150,150))
        d.text((x+6, y+6), str(gi), fill=(200,0,0), font=font)
        global_map.append((gi, os.path.basename(f)))
    outp = os.path.join(OUTDIR, f"walkman_grid_{g+1:02d}.png")
    canvas.save(outp)
    print(f"wrote {outp} ({len(chunk)} imgs)")
with open(os.path.join(OUTDIR, "index_map.txt"), "w") as fp:
    for gi, name in global_map:
        fp.write(f"{gi}\t{name}\n")
print(f"TOTAL={len(files)} GRIDS={grids}")
