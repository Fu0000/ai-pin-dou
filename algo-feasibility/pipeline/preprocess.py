"""Step 1: Preprocess.

EXIF rotation + size normalization + color space conversion.

Why this lives here (ADR-014 / docs/07-algo-spec.md §5.1):
    EXIF orientation is the #1 cause of "image is sideways" complaints
    when the rest of the pipeline is correct. We always normalize
    orientation here so downstream steps can assume RGB top-left origin.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

# 上限边长，防止 K-Means 在 4K 图上跑爆。降采样后再做后续步骤，损失可忽略。
MAX_LONG_SIDE = 1024


def preprocess(image_path: str | Path) -> np.ndarray:
    """Load image, fix EXIF orientation, downsize if huge, return RGB uint8 array.

    Args:
        image_path: path to source image (jpg/png/webp).

    Returns:
        np.ndarray of shape (H, W, 3), dtype=uint8, RGB color space.
    """
    img = Image.open(image_path)
    # 关键：EXIF 旋转必须在最早一步处理
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    long_side = max(img.size)
    if long_side > MAX_LONG_SIDE:
        ratio = MAX_LONG_SIDE / long_side
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    return np.asarray(img, dtype=np.uint8)
