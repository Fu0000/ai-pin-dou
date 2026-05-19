"""Build A/B/C/D side-by-side collages for human visual comparison."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
results_dirs = {
    "A baseline": ROOT / "data/results_a_baseline",
    "B +bilateral": ROOT / "data/results_b_bilateral",
    "C +bilateral+sat": ROOT / "data/results_c_bilateral_sat",
    "D +bilateral+sat+sharpen": ROOT / "data/results_d_full",
}
sample_ids = ["cat_03", "cat_11", "face_03", "face_06", "pet_07", "pet_03", "scene_00", "scene_07"]

tile = 200
cols = 1 + len(results_dirs)  # source + 4 configs
rows = len(sample_ids)
header_h = 30

canvas = Image.new("RGB", (tile * cols, tile * rows + header_h), (245, 245, 245))
draw = ImageDraw.Draw(canvas)

# Headers
headers = ["source"] + list(results_dirs.keys())
for i, h in enumerate(headers):
    draw.text((i * tile + 8, 6), h, fill=(60, 60, 60))

for r, sid in enumerate(sample_ids):
    src_path = list((ROOT / "samples").glob(f"*/{sid}.jpg"))
    if not src_path:
        continue
    src = Image.open(src_path[0]).convert("RGB").resize((tile, tile), Image.LANCZOS)
    canvas.paste(src, (0, header_h + r * tile))
    for c, (label, rd) in enumerate(results_dirs.items(), start=1):
        prv = Image.open(rd / sid / "preview.png").convert("RGB").resize((tile, tile), Image.NEAREST)
        canvas.paste(prv, (c * tile, header_h + r * tile))

out = ROOT / "data" / "_collage_compare.jpg"
canvas.save(out, quality=85)
print(f"saved {out}")
