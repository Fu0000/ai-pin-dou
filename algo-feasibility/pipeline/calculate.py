"""Step 8: Calculate (count beads per palette index)."""
from __future__ import annotations

from collections import Counter

import numpy as np


def calculate(index_grid: np.ndarray, palette_entries: list[dict]) -> dict:
    """Return color_summary dict and total bead count.

    Returns:
        {
          "total_cells": int,
          "foreground_cells": int,
          "color_count": int,
          "summary": [
            {"index": 12, "code": "M-023", "name": "玫瑰红", "count": 450},
            ...
          ]
        }
    """
    flat = index_grid.flatten()
    fg = flat[flat >= 0]
    counts = Counter(fg.tolist())
    summary = []
    for idx, cnt in counts.most_common():
        e = palette_entries[idx]
        summary.append(
            {
                "index": int(idx),
                "code": e.get("code", f"#{idx}"),
                "name": e.get("name", ""),
                "count": int(cnt),
            }
        )
    return {
        "total_cells": int(flat.size),
        "foreground_cells": int(fg.size),
        "color_count": len(counts),
        "summary": summary,
    }
