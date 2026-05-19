"""M0 dry-run batch executor (ADR-014).

Runs the full 8-step pipeline on every image under samples/<cat>/.
Captures per-step timing, memory delta, palette match quality, and
emits both a CSV and a JSON summary.

⚠️ This is a DRY-RUN with synthetic samples (or whatever sits in samples/).
It validates that the pipeline executes end-to-end and gives us a
performance baseline. It does NOT replace the human-graded M0 verdict
specified in docs/07-algo-spec.md §6.1.

Usage:
    uv run python run_dryrun.py
    uv run python run_dryrun.py --grid 32 --colors 16
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import psutil
from PIL import Image

from pipeline import run_pipeline
from pipeline.color_map import load_palette

ROOT = Path(__file__).resolve().parent
SAMPLES_DIR = ROOT / "samples"
RESULTS_DIR = ROOT / "data" / "results"
SCORING_CSV = ROOT / "scoring" / "score_pending.csv"


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round((len(s) - 1) * pct))))
    return s[k]


def _palette_distance_quality(index_grid: np.ndarray, palette_lab: np.ndarray) -> float:
    """Median CIE-Lab distance between adjacent foreground cells.

    Used as a 'visual smoothness' proxy. Lower means neighbors share similar
    colors → looks cleaner. Won't replace human scoring but useful objective signal.
    """
    g = index_grid.shape[0]
    distances = []
    for y in range(g):
        for x in range(g):
            cur = index_grid[y, x]
            if cur < 0:
                continue
            for dy, dx in ((1, 0), (0, 1)):
                ny, nx = y + dy, x + dx
                if ny < g and nx < g:
                    nb = index_grid[ny, nx]
                    if nb < 0 or nb == cur:
                        continue
                    d = palette_lab[cur] - palette_lab[nb]
                    distances.append(float(np.sqrt((d * d).sum())))
    if not distances:
        return 0.0
    return statistics.median(distances)


def render_preview(index_grid: np.ndarray, entries: list[dict], out_path: Path) -> None:
    g = index_grid.shape[0]
    arr = np.full((g, g, 3), 255, dtype=np.uint8)
    for y in range(g):
        for x in range(g):
            pi = int(index_grid[y, x])
            if pi >= 0:
                e = entries[pi]
                arr[y, x] = (e["r"], e["g"], e["b"])
    Image.fromarray(arr).resize((480, 480), Image.NEAREST).save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", type=int, default=48, help="grid size (default 48 = MVP normal)")
    parser.add_argument("--colors", type=int, default=24, help="K-Means cluster count")
    parser.add_argument("--no-cutout", action="store_true", help="ablation: skip rembg")
    parser.add_argument("--no-outline", action="store_true", help="ablation: skip outline step")
    parser.add_argument(
        "--no-stylize",
        action="store_true",
        help="disable lightweight cartoonization preprocess (ADR-029 v0.3 default ON)",
    )
    parser.add_argument(
        "--stylize-bilateral",
        action="store_true",
        default=True,
        help="enable cv2.bilateralFilter (default ON, ADR-029 v0.3)",
    )
    parser.add_argument(
        "--stylize-saturation",
        type=float,
        default=1.15,
        help="HSV saturation multiplier (default 1.15, ADR-029 v0.3)",
    )
    parser.add_argument(
        "--stylize-sharpen",
        action="store_true",
        help="enable unsharp mask (default OFF; A/B showed no benefit)",
    )
    parser.add_argument("--limit", type=int, default=0, help="cap N samples for quick test")
    parser.add_argument(
        "--label",
        type=str,
        default="",
        help="run label appended to output dir (e.g. 'a_baseline', 'b_bilateral')",
    )
    args = parser.parse_args()

    if args.label:
        global RESULTS_DIR
        RESULTS_DIR = ROOT / "data" / f"results_{args.label}"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    palette_entries, palette_lab = load_palette()
    print(f"palette loaded: {len(palette_entries)} colors")

    samples = []
    for cat_dir in sorted(SAMPLES_DIR.iterdir()):
        if not cat_dir.is_dir():
            continue
        for f in sorted(cat_dir.iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                samples.append((cat_dir.name, f))
    if args.limit > 0:
        samples = samples[: args.limit]
    print(f"running pipeline on {len(samples)} samples (grid={args.grid}, colors={args.colors})")

    proc = psutil.Process()
    rows: list[dict] = []
    started = time.perf_counter()

    for i, (cat, fp) in enumerate(samples):
        sample_id = f"{cat}_{fp.stem.split('_')[-1]}"
        out_dir = RESULTS_DIR / sample_id
        out_dir.mkdir(exist_ok=True)
        rss_before = proc.memory_info().rss / 1024 / 1024
        try:
            r = run_pipeline(
                fp,
                grid=args.grid,
                target_colors=args.colors,
                do_cutout=not args.no_cutout,
                do_outline=not args.no_outline,
                stylize_bilateral=args.stylize_bilateral and not args.no_stylize,
                stylize_saturation=args.stylize_saturation if not args.no_stylize else 1.0,
                stylize_sharpen=args.stylize_sharpen and not args.no_stylize,
            )
        except Exception as e:
            print(f"[{i+1}/{len(samples)}] ❌ {sample_id} -> {e}")
            traceback.print_exc(limit=3)
            rows.append(
                {
                    "sample_id": sample_id,
                    "category": cat,
                    "grid": args.grid,
                    "target_colors": args.colors,
                    "total_seconds": 99.999,
                    "score_1_to_5": "",
                    "notes": f"ERROR: {e}",
                }
            )
            continue
        rss_after = proc.memory_info().rss / 1024 / 1024
        np.save(out_dir / "index_grid.npy", r.index_grid)
        with open(out_dir / "color_summary.json", "w", encoding="utf-8") as f:
            json.dump(r.color_summary, f, ensure_ascii=False, indent=2)
        render_preview(r.index_grid, palette_entries, out_dir / "preview.png")

        smoothness = _palette_distance_quality(r.index_grid, palette_lab)

        row = {
            "sample_id": sample_id,
            "category": cat,
            "grid": args.grid,
            "target_colors": args.colors,
            "total_seconds": round(r.total_seconds, 3),
            "rss_delta_mb": round(rss_after - rss_before, 1),
            "color_count": r.color_summary["color_count"],
            "fg_cells": r.color_summary["foreground_cells"],
            "smoothness_lab_p50": round(smoothness, 2),
            "score_1_to_5": "",
            "notes": "",
        }
        for t in r.timings:
            row[f"step_{t.name}_ms"] = round(t.duration_ms, 1)
        rows.append(row)
        print(
            f"[{i+1}/{len(samples)}] ✅ {sample_id}  "
            f"total={r.total_seconds:.2f}s  colors={r.color_summary['color_count']}  "
            f"beads={r.color_summary['foreground_cells']}  rss+{rss_after - rss_before:.0f}MB"
        )

    if not rows:
        print("no samples processed", file=sys.stderr)
        return 1

    # CSV
    fields = sorted({k for r in rows for k in r.keys()})
    timing_csv = RESULTS_DIR / "timing_report.csv"
    with open(timing_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # Aggregate
    valid = [r for r in rows if r["total_seconds"] < 60]
    totals = [r["total_seconds"] for r in valid]
    summary = {
        "n_total": len(rows),
        "n_failed": len(rows) - len(valid),
        "wall_seconds": round(time.perf_counter() - started, 1),
        "p50_total_s": round(_percentile(totals, 0.5), 3),
        "p95_total_s": round(_percentile(totals, 0.95), 3),
        "p99_total_s": round(_percentile(totals, 0.99), 3),
        "p95_target_s": 10.0,
        "p95_pass": _percentile(totals, 0.95) <= 10.0 if totals else False,
        "median_smoothness_lab": round(
            statistics.median([r["smoothness_lab_p50"] for r in valid]), 2
        ),
        "step_p95_ms": {
            step: round(_percentile([r.get(f"step_{step}_ms", 0) for r in valid], 0.95), 1)
            for step in (
                "preprocess",
                "stylize",
                "cutout",
                "pixelize",
                "quantize",
                "color_map",
                "outline",
                "calculate",
            )
        },
        "args": {
            "grid": args.grid,
            "colors": args.colors,
            "no_cutout": args.no_cutout,
            "no_outline": args.no_outline,
            "stylize_bilateral": args.stylize_bilateral,
            "stylize_saturation": args.stylize_saturation,
            "stylize_sharpen": args.stylize_sharpen,
        },
        "by_category": {},
    }
    for cat in {r["category"] for r in valid}:
        cat_rows = [r for r in valid if r["category"] == cat]
        cat_totals = [r["total_seconds"] for r in cat_rows]
        summary["by_category"][cat] = {
            "n": len(cat_rows),
            "p95_s": round(_percentile(cat_totals, 0.95), 3),
            "median_colors": int(statistics.median([r["color_count"] for r in cat_rows])),
            "median_smoothness_lab": round(
                statistics.median([r["smoothness_lab_p50"] for r in cat_rows]), 2
            ),
        }

    summary_path = RESULTS_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Scoring CSV (template for human grading)
    SCORING_CSV.parent.mkdir(exist_ok=True)
    with open(SCORING_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["sample_id", "category", "grid", "target_colors", "total_seconds", "score_1_to_5", "notes"],
        )
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    k: r.get(k, "")
                    for k in (
                        "sample_id",
                        "category",
                        "grid",
                        "target_colors",
                        "total_seconds",
                        "score_1_to_5",
                        "notes",
                    )
                }
            )

    print("\n=== M0 dry-run summary ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\ntiming_report.csv -> {timing_csv}")
    print(f"summary.json      -> {summary_path}")
    print(f"score_template    -> {SCORING_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
