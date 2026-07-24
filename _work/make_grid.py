#!/usr/bin/env python3
"""Build an indexed image montage for manual clustering inspection."""
import sys, os
from PIL import Image, ImageDraw, ImageFont

def load(path, tw, th):
    im = Image.open(path).convert("RGB")
    im.thumbnail((tw, th), Image.LANCZOS)
    # pad to tw x th
    bg = Image.new("RGB", (tw, th), (255, 255, 255))
    bg.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    return bg

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir")
    ap.add_argument("--out")
    ap.add_argument("--files")  # optional: explicit file list (newline)
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--tw", type=int, default=160)
    ap.add_argument("--th", type=int, default=160)
    ap.add_argument("--border", type=int, default=6)
    ap.add_argument("--label", action="store_true")
    args = ap.parse_args()

    if args.files:
        with open(args.files) as f:
            names = [l.strip() for l in f if l.strip()]
        paths = [(os.path.join(args.indir, n) if args.indir else n) for n in names]
    else:
        paths = sorted(
            os.path.join(args.indir, f) for f in os.listdir(args.indir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        )

    cells = [load(p, args.tw, args.th) for p in paths]
    n = len(cells)
    cols = min(args.cols, n)
    rows = (n + cols - 1) // cols
    cw = args.tw + args.border
    ch = args.th + args.border
    W = cols * cw + args.border
    H = rows * ch + args.border
    canvas = Image.new("RGB", (W, H), (230, 230, 230))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    mapping = []
    for i, cell in enumerate(cells):
        r, c = divmod(i, cols)
        x = args.border + c * cw
        y = args.border + r * ch
        canvas.paste(cell, (x, y))
        d.rectangle([x, y, x + args.tw, y + args.th], outline=(180, 180, 180))
        if args.label:
            d.text((x + 3, y + 3), str(i + 1), fill=(220, 0, 0), font=font)
        mapping.append(os.path.basename(paths[i]))
    canvas.save(args.out)
    # print mapping index->filename
    with open(args.out + ".map.txt", "w") as f:
        for i, m in enumerate(mapping):
            f.write(f"{i+1}\t{m}\n")
    print(f"Wrote {args.out} ({cols}x{rows}, {n} images)")

if __name__ == "__main__":
    main()
