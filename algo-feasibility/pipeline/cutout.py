"""Step 2: Cutout (background removal).

Wraps rembg (ADR-003: open-source wrapping over self-built).
Choose `u2net_lite` for M0 to keep cold-start memory low (relevant to ADR-028
algo container memory cap).
"""
from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image
from rembg import new_session, remove

# Lazy-init session so import-time is fast in Notebook.
_session = None


def _get_session():
    global _session
    if _session is None:
        # u2net_lite 比 u2net 小 ~10x，速度快，质量略降但 M0 阶段够用。
        _session = new_session("u2netp")
    return _session


def cutout(rgb: np.ndarray, *, enabled: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Remove background, return RGBA cutout and alpha mask.

    Args:
        rgb: HxWx3 uint8 RGB array (from preprocess).
        enabled: if False, returns the input as opaque (skip cutout).
                 Lets us measure pipeline cost with/without cutout.

    Returns:
        (rgba, alpha):
            rgba: HxWx4 uint8, transparent background.
            alpha: HxW uint8 mask, 0=background, 255=foreground.
    """
    if not enabled:
        h, w = rgb.shape[:2]
        rgba = np.dstack([rgb, np.full((h, w), 255, dtype=np.uint8)])
        alpha = np.full((h, w), 255, dtype=np.uint8)
        return rgba, alpha

    img = Image.fromarray(rgb)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    out_bytes = remove(buf.read(), session=_get_session())
    out_img = Image.open(BytesIO(out_bytes)).convert("RGBA")
    rgba = np.asarray(out_img, dtype=np.uint8)
    alpha = rgba[:, :, 3]
    return rgba, alpha
