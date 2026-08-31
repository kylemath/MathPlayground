#!/usr/bin/env python3
"""Independent standard-library audit of an order-4 magic-square CSV."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
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


def is_magic(grid: Grid) -> bool:
    lines = [
        *(grid[offset : offset + 4] for offset in range(0, 16, 4)),
        *(grid[column::4] for column in range(4)),
        (grid[0], grid[5], grid[10], grid[15]),
        (grid[3], grid[6], grid[9], grid[12]),
    ]
    return sorted(grid) == list(range(1, 17)) and all(sum(line) == 34 for line in lines)


def load(path: Path) -> list[tuple[dict[str, str], Grid]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        (row, tuple(int(row[f"cell_{index}"]) for index in range(1, 17)))
        for row in rows
    ]


def audit(path: Path, enumerated_path: Path | None = None) -> dict[str, object]:
    records = load(path)
    grids = [grid for _, grid in records]
    canonical_grids = {canonical(grid) for grid in grids}
    oriented = {image for grid in grids for image in d4_images(grid)}
    by_canonical = {canonical(grid): row for row, grid in records}

    complement_consistent = 0
    complement_sentinel_consistent = 0
    for row, grid in records:
        complement_key = canonical(tuple(17 - value for value in grid))
        target = by_canonical.get(complement_key)
        source_id = int(row["id"])
        declared_id = int(row["complement_id"])
        if target is not None and declared_id == int(target["id"]):
            complement_consistent += 1
        if declared_id == 999 and complement_key == canonical(grid):
            complement_sentinel_consistent += 1
        elif declared_id != 999 and target is not None and declared_id == int(target["id"]):
            complement_sentinel_consistent += 1
        if declared_id == source_id and complement_key == canonical(grid):
            # Some source variants may use the source ID instead of a sentinel.
            complement_consistent += 0

    result: dict[str, object] = {
        "source": str(path.resolve()),
        "record_count": len(records),
        "ids_are_1_through_880": [int(row["id"]) for row, _ in records]
        == list(range(1, 881)),
        "all_normal_magic": all(is_magic(grid) for grid in grids),
        "unique_literal_grids": len(set(grids)),
        "unique_d4_canonical_grids": len(canonical_grids),
        "rows_already_lexicographically_canonical": sum(
            grid == canonical(grid) for grid in grids
        ),
        "d4_orbit_size_distribution": dict(
            sorted(Counter(len(d4_images(grid)) for grid in grids).items())
        ),
        "oriented_union_count": len(oriented),
        "complement_targets_present": sum(
            canonical(tuple(17 - value for value in grid)) in by_canonical
            for grid in grids
        ),
        "declared_complement_ids_directly_match": complement_consistent,
        "declared_complement_or_999_sentinel_consistent": complement_sentinel_consistent,
        "dudeney_group_distribution": dict(
            sorted(Counter(int(row["dudeney_group"]) for row, _ in records).items())
        ),
    }
    if enumerated_path is not None:
        enumerated = {
            tuple(int(value) for value in line.split(","))
            for line in enumerated_path.read_text(encoding="utf-8").splitlines()
            if line
        }
        result["enumerated_canonical_source"] = str(enumerated_path.resolve())
        result["enumerated_canonical_count"] = len(enumerated)
        result["csv_matches_from_scratch_enumeration"] = canonical_grids == enumerated
        result["csv_only_canonical_count"] = len(canonical_grids - enumerated)
        result["enumeration_only_canonical_count"] = len(enumerated - canonical_grids)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--enumerated", type=Path)
    args = parser.parse_args()
    result = audit(args.csv_path, args.enumerated)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
