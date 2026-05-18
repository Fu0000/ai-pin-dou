"""Step 5: Color map (snap each pixel to nearest Mard palette entry).

CIE Lab nearest-neighbor lookup. Output: a (g,g) int16 array of palette indices,
with -1 for background cells.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from skimage.color import rgb2lab

from .pixelize import BACKGROUND_SENTINEL

PALETTE_PATH = Path(__file__).resolve().parent.parent / "data" / "mard_palette.json"


def load_palette() -> tuple[list[dict], np.ndarray]:
    """Return (entries, lab_array) where lab_array.shape == (N, 3)."""
    with open(PALETTE_PATH, encoding="utf-8") as f:
        entries: list[dict] = json.load(f)
    rgb = np.array([[e["r"], e["g"], e["b"]] for e in entries], dtype=np.float32) / 255.0
    lab = rgb2lab(rgb.reshape(-1, 1, 3)).reshape(-1, 3)
    return entries, lab


def color_map(quantized_grid: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    """Map each foreground cell to its nearest palette entry.

    Returns:
        (index_grid, entries):
            index_grid: (g, g) int16, palette index per cell, -1 for background.
            entries: full palette list (for downstream calculate.py).
    """
    entries, palette_lab = load_palette()
    g, _, _ = quantized_grid.shape
    flat = quantized_grid.reshape(-1, 3).astype(np.int16)
    bg_mask = (flat == np.array(BACKGROUND_SENTINEL)).all(axis=1)

    rgb_norm = (flat.astype(np.float32) / 255.0).reshape(-1, 1, 3)
    lab = rgb2lab(rgb_norm).reshape(-1, 3)

    # nearest neighbor in Lab (vectorized)
    diff = lab[:, None, :] - palette_lab[None, :, :]
    dist = np.sum(diff * diff, axis=-1)
    indices = np.argmin(dist, axis=1).astype(np.int16)
    indices[bg_mask] = -1
    return indices.reshape(g, g), entries
