"""Step 3: Pixelize (downsample to grid).

Resize to NxN grid using box averaging. Background (alpha=0) becomes a
sentinel color and is excluded from quantize/calculate downstream.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

BACKGROUND_SENTINEL = (-1, -1, -1)  # marker, never appears in real palette


def pixelize(rgba: np.ndarray, alpha: np.ndarray, grid: int) -> np.ndarray:
    """Downsample RGBA to a grid x grid pixel matrix.

    Args:
        rgba: HxWx4 uint8 (output of cutout).
        alpha: HxW uint8.
        grid: target grid size, e.g. 32 / 48 / 64.

    Returns:
        np.ndarray of shape (grid, grid, 3), int16, where background cells
        are marked as BACKGROUND_SENTINEL.
    """
    img = Image.fromarray(rgba, mode="RGBA")
    # BOX averaging gives cleaner pixel art than NEAREST/LANCZOS for downsample.
    small = img.resize((grid, grid), Image.Resampling.BOX)
    arr = np.asarray(small, dtype=np.int16)  # (g,g,4)
    rgb = arr[:, :, :3]
    a = arr[:, :, 3]

    # Mark transparent cells as sentinel.
    rgb_with_bg = rgb.copy()
    bg_mask = a < 32  # alpha threshold
    rgb_with_bg[bg_mask] = np.array(BACKGROUND_SENTINEL, dtype=np.int16)
    return rgb_with_bg
