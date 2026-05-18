"""Step 7: Outline (anti-collapse darkening at object edges).

Heuristic: replace the outermost ring of foreground cells with the darkest
palette color in their neighborhood. Keeps the figure from "falling apart"
when ironed.

This is intentionally simple for M0; production iteration is in 07-algo-spec.md §5.7.
"""
from __future__ import annotations

import numpy as np


def outline(index_grid: np.ndarray, palette_entries: list[dict]) -> np.ndarray:
    """Darken edges where foreground meets background.

    Args:
        index_grid: (g, g) int16, palette indices, -1 for background.
        palette_entries: list of palette dicts with 'r','g','b' keys.

    Returns:
        new (g, g) int16 grid with edges replaced by darkest palette neighbor.
    """
    g = index_grid.shape[0]
    out = index_grid.copy()
    bg = -1
    luminance = np.array(
        [0.299 * e["r"] + 0.587 * e["g"] + 0.114 * e["b"] for e in palette_entries],
        dtype=np.float32,
    )

    for y in range(g):
        for x in range(g):
            cur = index_grid[y, x]
            if cur == bg:
                continue
            # check 4-neighborhood for any background → this is an edge cell
            is_edge = False
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < g and 0 <= nx < g and index_grid[ny, nx] == bg:
                    is_edge = True
                    break
            if not is_edge:
                continue
            # pick darker neighbor than current
            cur_lum = luminance[cur]
            candidates = [cur]
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < g and 0 <= nx < g:
                    nb = index_grid[ny, nx]
                    if nb != bg and luminance[nb] < cur_lum:
                        candidates.append(nb)
            out[y, x] = min(candidates, key=lambda i: luminance[i])
    return out
