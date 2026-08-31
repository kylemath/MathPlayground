#!/usr/bin/env python3
"""Verify 880 -> 7040 via explicit D4 expansion; compare to analyze.py formula."""

from __future__ import annotations

import csv
import json
from pathlib import Path

CSV = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv")
OUT = Path(__file__).resolve().parents[1] / "outputs" / "s1_orbit_expansion.json"


def rot(g: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(g[(3 - c) * 4 + r] for r in range(4) for c in range(4))


def flip_h(g: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(g[r * 4 + (3 - c)] for r in range(4) for c in range(4))


def d4_orbit(g: tuple[int, ...]) -> frozenset[tuple[int, ...]]:
    s: set[tuple[int, ...]] = set()
    cur = g
    for _ in range(4):
        s.add(cur)
        s.add(flip_h(cur))
        cur = rot(cur)
    return frozenset(s)


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    grids = [tuple(int(r[f"cell_{i}"]) for i in range(1, 17)) for r in rows]

    orbit_sizes = [len(d4_orbit(g)) for g in grids]
    oriented: set[tuple[int, ...]] = set()
    for g in grids:
        oriented |= set(d4_orbit(g))

    per_row_orbit_sum = sum(orbit_sizes)
    formula_7040 = len(grids) * 8

    result = {
        "csv_representatives": len(grids),
        "sum_of_orbit_sizes": per_row_orbit_sum,
        "unique_oriented_union": len(oriented),
        "analyze_py_formula_880_times_8": formula_7040,
        "all_orbits_size_8": all(s == 8 for s in orbit_sizes),
        "formula_matches_measured_union": formula_7040 == len(oriented),
        "note": (
            "analyze.py sets expandedOrientedCount = sourceCount * 8 (formula), "
            "not by measuring D4 expansion; this script measures the union."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
