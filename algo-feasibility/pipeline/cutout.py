"""Step 2: Cutout (background removal).

Wraps rembg (ADR-003: open-source wrapping over self-built).
Choose `u2netp` for M0 to keep cold-start memory low (relevant to ADR-028
algo container memory cap).

Foreground-presence fallback (ADR-029 v0.2):
    rembg u2netp, trained for 'subject vs background', misclassifies
    full-frame landscapes as 100% background. We measure the alpha
    foreground ratio and revert to the input image when it falls below
    a threshold, so quantize doesn't degenerate into a 1-color result.
"""
from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image
from rembg import new_session, remove

# Lazy-init session so import-time is fast in Notebook.
_session = None

#: Below this fraction the cutout is treated as 'no subject' and we
#: discard rembg's output (relevant to ADR-029 v0.2).
FG_RATIO_FALLBACK = 0.05


def _get_session():
    global _session
    if _session is None:
        # u2netp 比 u2net 小 ~10x，速度快，质量略降但 M0 阶段够用。
        _session = new_session("u2netp")
    return _session


def cutout(rgb: np.ndarray, *, enabled: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Remove background, with foreground-presence fallback.

    Args:
        rgb: HxWx3 uint8 RGB array (from preprocess).
        enabled: if False, returns the input as opaque (skip cutout).
                 Lets us measure pipeline cost with/without cutout.

    Returns:
        (rgba, alpha):
            rgba: HxWx4 uint8.
            alpha: HxW uint8 mask, 0=background, 255=foreground.

        When rembg's foreground ratio < FG_RATIO_FALLBACK, we treat the
        image as 'no subject' (e.g. a landscape) and return the original
        as fully opaque, so downstream steps see meaningful pixels.
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
    fg_ratio = float((alpha >= 128).mean())
    if fg_ratio < FG_RATIO_FALLBACK:
        # Subject-presence fallback (ADR-029 v0.2).
        # Treat as full-image content (e.g. landscape).
        h, w = rgb.shape[:2]
        rgba = np.dstack([rgb, np.full((h, w), 255, dtype=np.uint8)])
        alpha = np.full((h, w), 255, dtype=np.uint8)
    return rgba, alpha
