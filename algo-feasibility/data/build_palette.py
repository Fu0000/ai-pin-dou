"""Build mard_palette.json from upstream beadcolors CSV.

Source: https://github.com/maxcleme/beadcolors (gen/v3/mard.csv)
License: MIT (see LICENSE file in upstream repo)

Each row in the CSV is:
  code, code2, char, R, G, B, H, S, V, L, a, b, brand_label
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "mard.csv"
JSON_PATH = Path(__file__).resolve().parent / "mard_palette.json"


def main() -> int:
    if not CSV_PATH.exists():
        print(f"missing {CSV_PATH}", file=sys.stderr)
        return 1
    out = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 13:
                continue
            try:
                out.append(
                    {
                        "code": row[0].strip(),
                        "name": "",  # upstream CSV has no localized names
                        "r": int(row[3]),
                        "g": int(row[4]),
                        "b": int(row[5]),
                        "lab_l": float(row[9]),
                        "lab_a": float(row[10]),
                        "lab_b": float(row[11]),
                    }
                )
            except (ValueError, IndexError):
                continue
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(out)} entries to {JSON_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
