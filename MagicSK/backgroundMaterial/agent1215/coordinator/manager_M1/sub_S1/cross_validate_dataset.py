#!/usr/bin/env python3
"""Audit an 880-row CSV of D4-canonical normal order-4 magic squares."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

Grid = tuple[int, ...]
MAGIC = 34


def rotate_clockwise(grid: Grid) -> Grid:
    return tuple(grid[(3 - column) * 4 + row] for row in range(4) for column in range(4))


def reflect_left_right(grid: Grid) -> Grid:
    return tuple(grid[row * 4 + (3 - column)] for row in range(4) for column in range(4))


def d4_images(grid: Grid) -> set[Grid]:
    images: set[Grid] = set()
    current = grid
    for _ in range(4):
        images.add(current)
        images.add(reflect_left_right(current))
        current = rotate_clockwise(current)
    return images


def canonical(grid: Grid) -> Grid:
    return min(d4_images(grid))


def stabilizer_size(grid: Grid) -> int:
    return sum(1 for image in d4_images(grid) if image == grid)


def is_magic(grid: Grid) -> bool:
    lines = [
        *(grid[offset : offset + 4] for offset in range(0, 16, 4)),
        *(grid[column::4] for column in range(4)),
        (grid[0], grid[5], grid[10], grid[15]),
        (grid[3], grid[6], grid[9], grid[12]),
    ]
    return sorted(grid) == list(range(1, 17)) and all(sum(line) == MAGIC for line in lines)


def load(path: Path) -> list[tuple[dict[str, str], Grid]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        (row, tuple(int(row[f"cell_{index}"]) for index in range(1, 17)))
        for row in rows
    ]


def audit(path: Path) -> dict[str, object]:
    records = load(path)
    grids = [grid for _, grid in records]
    oriented = {image for grid in grids for image in d4_images(grid)}
    stabilizers = Counter(stabilizer_size(grid) for grid in grids)
    orbit_sizes = Counter(len(d4_images(grid)) for grid in grids)

    return {
        "source": str(path.resolve()),
        "record_count": len(records),
        "all_normal_magic": all(is_magic(grid) for grid in grids),
        "unique_literal_grids": len(set(grids)),
        "unique_d4_canonical_grids": len({canonical(grid) for grid in grids}),
        "rows_already_lexicographically_canonical": sum(grid == canonical(grid) for grid in grids),
        "d4_orbit_size_distribution_among_dataset_rows": dict(sorted(orbit_sizes.items())),
        "stabilizer_size_distribution_among_dataset_rows": dict(sorted(stabilizers.items())),
        "oriented_union_count_from_dataset_rows": len(oriented),
        "product_check_rows_times_8": len(grids) * 8 == len(oriented),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.csv_path)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
