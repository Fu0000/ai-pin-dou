"""Aggregate human scores into M0 verdict (ADR-014).

Usage:
    python scoring/score_summary.py scoring/score_template.csv

Output: PASS/FAIL verdict + breakdown by category.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

P95_TARGET_MS = 10_000  # docs/07-algo-spec.md §6.1
GOOD_RATE_TARGET = 0.60


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((len(s) - 1) * pct))
    return s[k]


def main(path: str) -> int:
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if not r.get("sample_id") or r["sample_id"].startswith("#"):
                continue
            try:
                r["score_1_to_5"] = int(r["score_1_to_5"])
                r["total_seconds"] = float(r["total_seconds"])
            except (ValueError, KeyError):
                continue
            rows.append(r)

    if not rows:
        print("[FAIL] No scored rows found.", file=sys.stderr)
        return 1

    overall_p95_ms = percentile([r["total_seconds"] * 1000 for r in rows], 0.95)
    overall_good = sum(1 for r in rows if r["score_1_to_5"] >= 3) / len(rows)

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cat[r.get("category", "other")].append(r)

    cat_breakdown = {}
    for cat, items in by_cat.items():
        cat_breakdown[cat] = {
            "n": len(items),
            "good_rate": round(sum(1 for r in items if r["score_1_to_5"] >= 3) / len(items), 3),
            "p95_ms": round(percentile([r["total_seconds"] * 1000 for r in items], 0.95), 1),
        }

    verdict = (
        "PASS"
        if overall_p95_ms <= P95_TARGET_MS and overall_good >= GOOD_RATE_TARGET
        else "FAIL"
    )

    report = {
        "n_total": len(rows),
        "p95_total_ms": round(overall_p95_ms, 1),
        "p95_target_ms": P95_TARGET_MS,
        "good_rate": round(overall_good, 3),
        "good_rate_target": GOOD_RATE_TARGET,
        "verdict": verdict,
        "category_breakdown": cat_breakdown,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_summary.py scoring/score_template.csv", file=sys.stderr)
        sys.exit(64)
    sys.exit(main(sys.argv[1]))
