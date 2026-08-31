#!/usr/bin/env python3
"""Audit entrywise complement involution on D4-canonical classes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

Grid = tuple[int, ...]


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


def complement(grid: Grid) -> Grid:
    return tuple(17 - value for value in grid)


def load(path: Path) -> list[tuple[int, Grid, int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        (
            int(row["id"]),
            tuple(int(row[f"cell_{index}"]) for index in range(1, 17)),
            int(row["complement_id"]),
        )
        for row in rows
    ]


def audit(path: Path) -> dict[str, object]:
    records = load(path)
    by_canonical = {canonical(grid): row_id for row_id, grid, _ in records}

    fixed_classes = 0
    two_cycles = 0
    visited: set[Grid] = set()

    for _, grid, _ in records:
        key = canonical(grid)
        if key in visited:
            continue
        comp_key = canonical(complement(grid))
        if comp_key == key:
            fixed_classes += 1
            visited.add(key)
        else:
            two_cycles += 1
            visited.add(key)
            visited.add(comp_key)

    declared_ok = 0
    for row_id, grid, declared in records:
        comp_key = canonical(complement(grid))
        if comp_key == canonical(grid):
            if declared in (999, row_id):
                declared_ok += 1
        elif declared == by_canonical.get(comp_key):
            declared_ok += 1

    return {
        "source": str(path.resolve()),
        "record_count": len(records),
        "fixed_d4_classes_under_complement": fixed_classes,
        "two_cycles_among_remaining_classes": two_cycles,
        "classes_in_two_cycles": two_cycles * 2,
        "complement_orbits_total": fixed_classes + two_cycles,
        "check_fixed_plus_paired_equals_880": fixed_classes + two_cycles * 2 == 880,
        "declared_complement_ids_consistent": declared_ok == len(records),
        "note": (
            "Complement acts on values (x -> 17-x), then re-canonicalize under D4. "
            "This is separate from the D4 quotient itself."
        ),
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
