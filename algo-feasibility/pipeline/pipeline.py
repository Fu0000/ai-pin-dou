"""Main 8-step pipeline orchestrator (ADR-014 / docs/07-algo-spec.md §1.1).

Returns timing for each step so we can identify the slow phase during
M0 feasibility testing.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .calculate import calculate
from .color_map import color_map
from .cutout import cutout
from .outline import outline
from .pixelize import pixelize
from .preprocess import preprocess
from .quantize import quantize
from .stylize import stylize


@dataclass
class StepTiming:
    name: str
    duration_ms: float


@dataclass
class PipelineResult:
    sample_path: str
    grid: int
    target_colors: int
    color_summary: dict
    index_grid: np.ndarray
    timings: list[StepTiming] = field(default_factory=list)
    total_ms: float = 0.0

    @property
    def total_seconds(self) -> float:
        return self.total_ms / 1000.0


def _tick(label: str, t0: float, timings: list[StepTiming]) -> float:
    now = time.perf_counter()
    timings.append(StepTiming(name=label, duration_ms=(now - t0) * 1000))
    return now


def run_pipeline(
    image_path: str | Path,
    *,
    grid: int = 48,
    target_colors: int = 24,
    do_cutout: bool = True,
    do_outline: bool = True,
    stylize_bilateral: bool = True,
    stylize_saturation: float = 1.15,
    stylize_sharpen: bool = False,
) -> PipelineResult:
    """Execute the full 8-step pipeline on a single image.

    Defaults reflect ADR-029 v0.3 (lightweight cartoonization preprocess):
        bilateral=True, saturation=1.15, sharpen=False.

    Args:
        image_path: source photo (any format Pillow supports).
        grid: pixel grid size (e.g. 32/48/64).
        target_colors: K-Means cluster count before snapping to Mard palette.
        do_cutout: if False, skip background removal (faster, for ablation).
        do_outline: if False, skip step 7.
        stylize_bilateral: enable cv2.bilateralFilter (default on, ADR-029 v0.3).
        stylize_saturation: HSV S-channel multiplier (default 1.15).
        stylize_sharpen: enable unsharp mask (default off; A/B showed no benefit).

    Returns:
        PipelineResult with timings and color_summary.
    """
    timings: list[StepTiming] = []
    overall_start = time.perf_counter()
    t = overall_start

    # ① Preprocess
    rgb = preprocess(image_path)
    t = _tick("preprocess", t, timings)

    # ②.5 Stylize (lightweight cartoonization, ADR-029 v0.3)
    do_stylize = stylize_bilateral or abs(stylize_saturation - 1.0) > 1e-3 or stylize_sharpen
    if do_stylize:
        rgb = stylize(
            rgb,
            bilateral=stylize_bilateral,
            saturation=stylize_saturation,
            sharpen=stylize_sharpen,
        )
        t = _tick("stylize", t, timings)

    # ② Cutout
    rgba, alpha = cutout(rgb, enabled=do_cutout)
    t = _tick("cutout", t, timings)

    # ③ Pixelize
    pixel_grid = pixelize(rgba, alpha, grid)
    t = _tick("pixelize", t, timings)

    # ④ Quantize
    quantized = quantize(pixel_grid, target_colors)
    t = _tick("quantize", t, timings)

    # ⑤ ColorMap
    index_grid, palette_entries = color_map(quantized)
    t = _tick("color_map", t, timings)

    # ⑥ Constraint (库存约束) — M0 阶段先跳过，等 Phase 1 接 RDS 时再实现
    # ⑦ Outline
    if do_outline:
        index_grid = outline(index_grid, palette_entries)
        t = _tick("outline", t, timings)

    # ⑧ Calculate
    color_summary = calculate(index_grid, palette_entries)
    t = _tick("calculate", t, timings)

    total_ms = (time.perf_counter() - overall_start) * 1000
    return PipelineResult(
        sample_path=str(image_path),
        grid=grid,
        target_colors=target_colors,
        color_summary=color_summary,
        index_grid=index_grid,
        timings=timings,
        total_ms=total_ms,
    )
