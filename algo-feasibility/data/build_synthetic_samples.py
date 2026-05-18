"""Generate synthetic test samples for M0 dry-run.

⚠️ THESE ARE NOT REAL PHOTOS.
They serve as a smoke-test baseline so the pipeline can be verified end-to-end
before real human photos are available. ADR-014 requires real photos for the
final M0 verdict.

Strategy: 4 synthetic categories that mimic the real-world challenges:
  - "geo": geometric subjects on solid bg (easiest case)
  - "blob": soft organic blobs with gradient bg (mid)
  - "complex": multi-color subjects + gradient bg (harder)
  - "noisy": complex subjects + photo grain (hardest)

Each category produces 25 images at 800x800 (representative of mobile photo size).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "samples"
SIZE = (800, 800)
SEED = 42


def _rand_color(rng: random.Random, vivid: bool = False) -> tuple[int, int, int]:
    if vivid:
        # ensure saturation is high
        h = rng.random()
        s = 0.6 + rng.random() * 0.4
        v = 0.7 + rng.random() * 0.3
        # HSV -> RGB
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        i %= 6
        rgb = [
            (v, t, p),
            (q, v, p),
            (p, v, t),
            (p, q, v),
            (t, p, v),
            (v, p, q),
        ][i]
        return tuple(int(c * 255) for c in rgb)
    return tuple(rng.randint(20, 235) for _ in range(3))


def _gradient_bg(rng: random.Random) -> Image.Image:
    a = _rand_color(rng)
    b = _rand_color(rng)
    img = Image.new("RGB", SIZE, a)
    arr = np.zeros((SIZE[1], SIZE[0], 3), dtype=np.uint8)
    for y in range(SIZE[1]):
        t = y / SIZE[1]
        for c in range(3):
            arr[y, :, c] = int(a[c] * (1 - t) + b[c] * t)
    return Image.fromarray(arr)


def _add_noise(img: Image.Image, sigma: int) -> Image.Image:
    arr = np.asarray(img, dtype=np.int16)
    noise = np.random.normal(0, sigma, arr.shape).astype(np.int16)
    out = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def gen_geo(idx: int, rng: random.Random) -> Image.Image:
    img = Image.new("RGB", SIZE, _rand_color(rng))
    d = ImageDraw.Draw(img)
    # 2~4 color blocks
    for _ in range(rng.randint(2, 4)):
        shape = rng.choice(["circle", "rect", "triangle"])
        c = _rand_color(rng, vivid=True)
        x0 = rng.randint(50, SIZE[0] - 250)
        y0 = rng.randint(50, SIZE[1] - 250)
        s = rng.randint(120, 280)
        if shape == "circle":
            d.ellipse([x0, y0, x0 + s, y0 + s], fill=c)
        elif shape == "rect":
            d.rectangle([x0, y0, x0 + s, y0 + s], fill=c)
        else:
            d.polygon([(x0 + s // 2, y0), (x0, y0 + s), (x0 + s, y0 + s)], fill=c)
    return img


def gen_blob(idx: int, rng: random.Random) -> Image.Image:
    img = _gradient_bg(rng)
    d = ImageDraw.Draw(img)
    # one big organic blob
    cx, cy = SIZE[0] // 2 + rng.randint(-100, 100), SIZE[1] // 2 + rng.randint(-100, 100)
    pts = []
    for a in range(0, 360, 20):
        r = 200 + rng.randint(-60, 60)
        rad = a * np.pi / 180
        pts.append((cx + r * np.cos(rad), cy + r * np.sin(rad)))
    d.polygon(pts, fill=_rand_color(rng, vivid=True))
    return img.filter(ImageFilter.GaussianBlur(radius=2))


def gen_complex(idx: int, rng: random.Random) -> Image.Image:
    img = _gradient_bg(rng)
    d = ImageDraw.Draw(img)
    # multiple overlapping blobs
    for _ in range(rng.randint(3, 6)):
        cx, cy = rng.randint(150, SIZE[0] - 150), rng.randint(150, SIZE[1] - 150)
        r = rng.randint(80, 200)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_rand_color(rng, vivid=True))
    return img.filter(ImageFilter.GaussianBlur(radius=3))


def gen_noisy(idx: int, rng: random.Random) -> Image.Image:
    img = gen_complex(idx, rng)
    return _add_noise(img, sigma=rng.randint(20, 40))


GENERATORS = {
    "geo": gen_geo,
    "blob": gen_blob,
    "complex": gen_complex,
    "noisy": gen_noisy,
}


def main() -> int:
    if SAMPLES_DIR.exists() and any(SAMPLES_DIR.iterdir()):
        # Idempotent: skip if anything exists in samples/
        # Real photos might already be there; refuse to overwrite.
        for cat in GENERATORS:
            cat_dir = SAMPLES_DIR / cat
            if cat_dir.exists() and any(cat_dir.glob("*.png")):
                print(f"⚠️ {cat_dir} already populated; skipping (delete to regenerate)")
                return 0

    rng = random.Random(SEED)
    np.random.seed(SEED)
    total = 0
    for cat, gen in GENERATORS.items():
        cat_dir = SAMPLES_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        for i in range(25):
            img = gen(i, rng)
            img.save(cat_dir / f"{cat}_{i:02d}.png", optimize=True)
            total += 1
    print(f"generated {total} synthetic samples under {SAMPLES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
