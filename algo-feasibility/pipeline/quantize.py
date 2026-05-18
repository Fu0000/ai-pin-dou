"""Step 4: Color quantize (K-Means in CIE Lab space).

Why Lab not RGB:
    Euclidean distance in Lab space approximates perceptual color distance.
    RGB distance routinely picks the "wrong" color when matching to a fixed
    palette (relevant to coding-standards §8.1).
"""
from __future__ import annotations

import numpy as np
from skimage.color import lab2rgb, rgb2lab
from sklearn.cluster import MiniBatchKMeans

from .pixelize import BACKGROUND_SENTINEL


def quantize(pixel_grid: np.ndarray, n_colors: int, *, seed: int = 0) -> np.ndarray:
    """Reduce a (g,g,3) pixel grid to at most n_colors distinct colors.

    Background cells (BACKGROUND_SENTINEL) are preserved untouched.

    Returns:
        (g, g, 3) int16, quantized RGB values; background cells unchanged.
    """
    g, _, _ = pixel_grid.shape
    flat = pixel_grid.reshape(-1, 3).astype(np.int16)
    bg_mask = (flat == np.array(BACKGROUND_SENTINEL)).all(axis=1)
    fg = flat[~bg_mask]

    if len(fg) == 0:
        return pixel_grid.copy()

    # RGB -> Lab
    fg_rgb_norm = (fg.astype(np.float32) / 255.0).reshape(-1, 1, 3)
    fg_lab = rgb2lab(fg_rgb_norm).reshape(-1, 3)

    actual_k = min(n_colors, max(1, len(fg)))
    km = MiniBatchKMeans(n_clusters=actual_k, random_state=seed, n_init=10, batch_size=1024)
    labels = km.fit_predict(fg_lab)
    centers_lab = km.cluster_centers_

    # Lab -> RGB
    centers_rgb = (lab2rgb(centers_lab.reshape(-1, 1, 3)) * 255).reshape(-1, 3).astype(np.int16)
    fg_q = centers_rgb[labels]

    out = flat.copy()
    out[~bg_mask] = fg_q
    return out.reshape(g, g, 3)
