"""Pixel-level diff analysis between A/B/C/D runs.

Quantifies how much each preprocess option actually changes the
final pattern, beyond what the smoothness_lab metric reveals.

For each sample we compute index_grid agreement rates and saturation
of the rendered preview.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.color import rgb2hsv

ROOT = Path(__file__).resolve().parent.parent
configs = ["a_baseline", "b_bilateral", "c_bilateral_sat", "d_full"]
results = {c: ROOT / f"data/results_{c}" for c in configs}

# Find samples present in all configs
all_sids = sorted(p.name for p in results["a_baseline"].iterdir() if p.is_dir())

stats = {c: {"agree_with_a": [], "satur_pct50": [], "n_unique_colors": []} for c in configs}

for sid in all_sids:
    grids = {}
    previews = {}
    for c in configs:
        gp = results[c] / sid / "index_grid.npy"
        pp = results[c] / sid / "preview.png"
        if not gp.exists() or not pp.exists():
            grids = {}
            break
        grids[c] = np.load(gp)
        previews[c] = np.asarray(Image.open(pp).convert("RGB"))
    if not grids:
        continue

    base = grids["a_baseline"]
    for c in configs:
        agree = float((grids[c] == base).mean())
        stats[c]["agree_with_a"].append(agree)
        rgb = previews[c].astype(np.float32) / 255.0
        # only count non-white pixels
        nonwhite = ~((rgb > 0.98).all(axis=-1))
        if nonwhite.any():
            hsv = rgb2hsv(rgb)
            stats[c]["satur_pct50"].append(float(np.median(hsv[..., 1][nonwhite])))
        flat = previews[c].reshape(-1, 3)
        # exclude pure white (background)
        nonwhite_flat = flat[~((flat == 255).all(axis=1))]
        stats[c]["n_unique_colors"].append(
            len(np.unique(nonwhite_flat, axis=0)) if len(nonwhite_flat) else 0
        )

import statistics

print(f'{"config":<25}  agree(grid)  satur_p50  uniq_colors')
print("-" * 70)
for c in configs:
    s = stats[c]
    agree = statistics.median(s["agree_with_a"]) if s["agree_with_a"] else 0
    sat = statistics.median(s["satur_pct50"]) if s["satur_pct50"] else 0
    uc = statistics.median(s["n_unique_colors"]) if s["n_unique_colors"] else 0
    print(f"{c:<25}  {agree:>11.3f}  {sat:>9.3f}  {uc:>11}")

print()
# Per-category breakdown of how much a/b/c/d agree
import csv

rows = list(csv.DictReader(open(results["a_baseline"] / "timing_report.csv")))
sid_to_cat = {r["sample_id"]: r["category"] for r in rows}
print("By-category disagreement vs A (lower agree = bigger pipeline change):")
for cat in ("cat", "face", "pet", "scene"):
    print(f"\n  {cat}:")
    for c in configs:
        agreements = [
            v
            for sid, v in zip(all_sids, stats[c]["agree_with_a"])
            if sid_to_cat.get(sid) == cat
        ]
        if agreements:
            print(f"    {c:<22}  median agree = {statistics.median(agreements):.3f}")
