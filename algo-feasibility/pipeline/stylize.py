"""Step 2.5: Lightweight stylize (preprocess for low-resolution discrete media).

Why this step exists:
    Perler beads are physically a low-resolution, discrete-color medium
    (32x32 ~ 64x64 grids of fixed palette colors). Pushing a noisy
    photo with smooth gradients through K-Means + nearest-palette
    snap creates muddy, low-contrast results. A light "cartoonization"
    preprocess flattens noise and bumps saturation so the limited
    output bandwidth carries the perceptually important parts.

What we do (cheap, deterministic):
    1. Bilateral filter — denoise while preserving edges
    2. HSV saturation boost — compensate for the desaturation that
       palette-snapping causes
    3. Optional unsharp mask — emphasize edges before downsampling

What we explicitly DO NOT do here:
    - Style-transfer GANs (AnimeGAN, White-box Cartoonization, etc.)
    - These belong in the "Cartoon" style variant per ADR-019, not
      in the default preprocess. Default must preserve recognizability
      of the user's actual subject (ADR-013 灵魂 #2).

Performance budget: <= 50ms per image at 1024px long side.

ADR refs: ADR-013 (preserve recognizability), ADR-019 (cartoon = variant
not default), ADR-029 v0.3 (this step's introduction).
"""
from __future__ import annotations

import cv2
import numpy as np


def stylize(
    rgb: np.ndarray,
    *,
    bilateral: bool = True,
    saturation: float = 1.15,
    sharpen: bool = False,
) -> np.ndarray:
    """Apply lightweight cartoonization to an RGB image.

    Args:
        rgb: HxWx3 uint8 RGB array.
        bilateral: apply edge-preserving denoise.
        saturation: HSV S-channel multiplier (1.0 = identity, >1.0 = more vivid).
                   Use 1.15 ~ 1.25 for "vivid but still natural".
        sharpen: apply unsharp mask before output (compensates downsample blur).

    Returns:
        HxWx3 uint8 RGB.
    """
    out = rgb

    if bilateral:
        # d=9 covers ~9px neighborhood; sigmaColor 75 in 0-255 space
        # smooths flat areas while keeping subject edges crisp.
        # cv2 expects BGR but bilateral is channel-agnostic in practice;
        # we work in RGB and trust the algorithm.
        out = cv2.bilateralFilter(out, d=9, sigmaColor=75, sigmaSpace=75)

    if abs(saturation - 1.0) > 1e-3:
        hsv = cv2.cvtColor(out, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * saturation, 0, 255)
        out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    if sharpen:
        # Standard unsharp mask: blur, then add the difference back.
        blurred = cv2.GaussianBlur(out, (0, 0), sigmaX=1.5)
        out = cv2.addWeighted(out, 1.4, blurred, -0.4, 0)

    return out
