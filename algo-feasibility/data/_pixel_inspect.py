"""Inspect specific samples cell-by-cell to gauge perceptual change."""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
configs = ["a_baseline", "b_bilateral", "c_bilateral_sat", "d_full"]


def cell_features(preview_path: Path) -> dict:
    img = np.asarray(Image.open(preview_path).convert("RGB").resize((48, 48), Image.NEAREST))
    flat = img.reshape(-1, 3).astype(np.int32)
    non_white = flat[~((flat == 255).all(axis=1))]
    if len(non_white) == 0:
        return {"n": 0}
    return {
        "n": len(non_white),
        "rgb_mean": tuple(int(x) for x in non_white.mean(axis=0)),
        "rgb_max_per_chan": tuple(int(x) for x in non_white.max(axis=0)),
        "saturation_proxy": int(
            np.mean(non_white.max(axis=1) - non_white.min(axis=1))
        ),  # range as cheap saturation proxy
    }


for sid in ("cat_03", "face_06", "pet_07", "scene_00"):
    print(f"\n=== {sid} ===")
    for c in configs:
        p = ROOT / f"data/results_{c}/{sid}/preview.png"
        if p.exists():
            print(f"  {c:<22}", cell_features(p))
