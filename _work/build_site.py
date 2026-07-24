#!/usr/bin/env python3
# Build the Hugo gallery content from the vision-derived model assignments.
import os, shutil, glob, datetime

ROOT = "/home/luke/programming/sites/repair_man"
WALK_DIR = "/run/media/luke/e0c64a5a-108c-4b5d-970c-737155040554/Pictures/Phone Backup/Photos/Walkman"
CRT_DIR  = "/run/media/luke/e0c64a5a-108c-4b5d-970c-737155040554/Pictures/Phone Backup/Photos/CRT"
CONTENT = os.path.join(ROOT, "content", "galleries")

# slug -> (title, technology format, approx year, [categories])
MODELS = {
    "wm-10":          ("Sony WM-10",          "Compact Cassette — Portable Player",                  1982, ["Walkman", "Sony"]),
    "wm-f10":         ("Sony WM-F10",         "Compact Cassette — Portable Player (FM)",             1983, ["Walkman", "Sony"]),
    "wm-100":         ("Sony WM-100",         "Compact Cassette — Portable Player (AM/FM)",          1983, ["Walkman", "Sony"]),
    "wm-f100":        ("Sony WM-F100",        "Compact Cassette — Portable Player (AM/FM, Auto-Reverse)", 1983, ["Walkman", "Sony"]),
    "wm-f18":         ("Sony WM-F18",         "Compact Cassette — Portable Player (AM/FM, Auto-Reverse)", 1987, ["Walkman", "Sony"]),
    "wm-f77":         ("Sony WM-F77",         "Compact Cassette — Portable Player (AM/FM, Auto-Reverse)", 1988, ["Walkman", "Sony"]),
    "aiwa-hs-g600":   ("AIWA HS-G600",        "Compact Cassette — Portable Player",                  1985, ["Walkman", "AIWA"]),
    "crt-sony-tv":    ("Sony Trinitron CRT Television", "CRT Television",                             1995, ["CRT", "CRT Television"]),
    "crt-tv-unbranded": ("CRT Television",    "CRT Television",                                      1990, ["CRT", "CRT Television"]),
    "crt-imac-g3":    ("Apple iMac G3 (CRT)", "CRT Monitor (All-in-One)",                            1998, ["CRT", "CRT Monitor"]),
    "crt-compaq":     ("Compaq CRT Monitor",  "CRT Monitor",                                         1998, ["CRT", "CRT Monitor"]),
    "crt-monitor-beige": ("CRT Monitor",      "CRT Monitor",                                         1995, ["CRT", "CRT Monitor"]),
}

# gid (1-based, sorted dir order, Screenshots excluded) -> [slugs]; absent/None = skip
WALK = {
    2:["wm-10"],3:["wm-f18"],4:["wm-f100"],8:["wm-f10"],9:["aiwa-hs-g600"],10:["wm-f77"],
    21:["wm-10"],23:["wm-100"],24:["wm-100"],25:["wm-100"],26:["wm-f18"],27:["wm-f10"],
    28:["wm-f100"],29:["wm-f77"],30:["wm-f10"],31:["aiwa-hs-g600"],
    41:["wm-f100"],42:["wm-f100"],43:["wm-f100"],44:["wm-f100"],45:["wm-f100"],46:["wm-f100"],
    47:["wm-f100"],48:["wm-f100"],49:["wm-f100"],50:["wm-f100"],51:["wm-f100"],52:["wm-f100"],
    53:["wm-f100"],54:["wm-f100"],55:["wm-f100"],56:["wm-f100"],57:["wm-f100"],58:["wm-f100"],
    59:["wm-f100"],60:["wm-f100"],
    65:["wm-f10"],66:["wm-f100"],76:["wm-f18"],77:["wm-f77"],78:["wm-10"],79:["wm-10"],80:["wm-f77"],
    81:["wm-f10"],82:["wm-f10"],83:["wm-10"],84:["wm-f18"],85:["wm-f18"],86:["wm-f77"],87:["wm-10"],
    88:["wm-100"],89:["wm-f18"],91:["wm-f18"],96:["wm-10"],97:["wm-10"],
    103:["wm-f100"],104:["wm-f100"],105:["wm-f100"],106:["wm-100"],107:["wm-f10"],108:["aiwa-hs-g600"],
    109:["wm-f100"],110:["wm-10"],111:["wm-f10"],112:["wm-f10"],113:["wm-f10"],115:["wm-f10"],116:["wm-f10"],
    120:["wm-f100"],121:["wm-10"],122:["wm-f18"],123:["wm-f77"],124:["wm-f100"],
    129:["wm-f100"],130:["wm-10"],133:["aiwa-hs-g600"],134:["wm-100"],
    141:["wm-f100"],142:["wm-f100"],143:["wm-f100"],144:["wm-f100"],145:["wm-10"],148:["wm-f100"],
    149:["wm-10"],150:["wm-10"],152:["wm-100"],153:["wm-f10"],154:["wm-f10"],155:["wm-f10"],156:["wm-f10"],
    159:["wm-f10"],
    161:["wm-f10"],
    162:["wm-f10","wm-100","wm-f18","wm-f77"],
    163:["wm-f10","wm-f100","wm-f18","wm-f77"],
    164:["wm-f10","wm-f100","wm-10","wm-f18"],
    165:["wm-f10","wm-f100","wm-f18","wm-f77"],
    166:["wm-f10","wm-f100","wm-10","wm-f18"],
    167:["wm-f10","wm-10","wm-f18","wm-f77"],
    168:["wm-10","wm-f10","wm-f18","wm-100"],
    169:["wm-10","wm-f10","wm-f18","wm-f77"],
    170:["wm-f10","wm-100","wm-f18","aiwa-hs-g600"],
    171:["wm-f10","wm-f100","wm-f18","wm-f77"],
    172:["wm-f10","wm-100"],
    173:["wm-10"],174:["wm-f100"],175:["wm-f77"],176:["wm-f18"],177:["wm-f18"],178:["wm-f77"],
    179:["wm-f10"],180:["wm-f18"],
    181:["wm-10"],182:["wm-100"],183:["wm-f10"],186:["wm-f18"],189:["wm-f77"],191:["aiwa-hs-g600"],
    196:["wm-f18"],197:["wm-f18"],
}

CRT = {
    1:["crt-sony-tv"],2:["crt-sony-tv"],3:["crt-sony-tv"],4:["crt-sony-tv"],9:["crt-sony-tv"],10:["crt-sony-tv"],
    5:["crt-tv-unbranded"],6:["crt-tv-unbranded"],7:["crt-tv-unbranded"],8:["crt-tv-unbranded"],22:["crt-tv-unbranded"],
    11:["crt-imac-g3"],13:["crt-imac-g3"],21:["crt-imac-g3"],
    14:["crt-compaq"],15:["crt-compaq"],24:["crt-compaq"],
    16:["crt-monitor-beige"],17:["crt-monitor-beige"],18:["crt-monitor-beige"],19:["crt-monitor-beige"],
    20:["crt-monitor-beige"],23:["crt-monitor-beige"],
}

def list_sorted(d):
    files = sorted(glob.glob(os.path.join(d, "*.jpg")) +
                   glob.glob(os.path.join(d, "*.jpeg")) +
                   glob.glob(os.path.join(d, "*.png")))
    return [f for f in files if "Screenshot" not in os.path.basename(f)]

def slugify_title(t):
    return t.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-")

def main():
    walk_files = list_sorted(WALK_DIR)
    crt_files = list_sorted(CRT_DIR)
    # assignment accumulator: slug -> [(srcpath, prefix)]
    acc = {s: [] for s in MODELS}
    for gid, slugs in WALK.items():
        src = walk_files[gid-1]
        for s in slugs:
            acc[s].append((src, gid))
    for gid, slugs in CRT.items():
        src = crt_files[gid-1]
        for s in slugs:
            acc[s].append((src, gid))

    os.makedirs(CONTENT, exist_ok=True)
    for slug, (title, fmt, year, cats) in MODELS.items():
        imgs = acc[slug]
        if not imgs:
            print(f"SKIP {slug} (no images)")
            continue
        gdir = os.path.join(CONTENT, slug)
        os.makedirs(gdir, exist_ok=True)
        # copy images (prefixed with gid to guarantee unique names)
        for src, gid in imgs:
            dst = os.path.join(gdir, f"{gid:03d}_{os.path.basename(src)}")
            shutil.copy2(src, dst)
        # write index.md
        cats_str = ", ".join(f'"{c}"' for c in cats)
        body = (
            f"Device: {title}\n"
            f"Technology: {fmt}\n"
            f"Approx. year: {year}\n\n"
            f"_Photo captions to be added._\n"
        )
        md = (
            "---\n"
            f'title: "{title}"\n'
            f'date: {year}-01-01\n'
            f"categories: [{cats_str}]\n"
            "---\n\n"
            f"{body}"
        )
        with open(os.path.join(gdir, "index.md"), "w") as f:
            f.write(md)
        print(f"OK {slug}: {len(imgs)} images -> {title}")

if __name__ == "__main__":
    main()
