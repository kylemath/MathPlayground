#!/usr/bin/env python3
"""Deterministically enumerate and classify normal order-4 magic squares.

Standard library only. Rows are selected from the 86 four-element subsets of
1..16 that sum to 34. Three ordered rows determine the fourth by column sums.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from collections import Counter
from pathlib import Path

N = 4
MAGIC = 34
COMPLEMENT = 17
FULL_MASK = (1 << 16) - 1
Grid = tuple[int, ...]
Row = tuple[int, ...]


def value_mask(values: tuple[int, ...]) -> int:
    mask = 0
    for value in values:
        if not 1 <= value <= 16:
            return -1
        bit = 1 << (value - 1)
        if mask & bit:
            return -1
        mask |= bit
    return mask


def enumerate_oriented() -> list[Grid]:
    row_masks: dict[int, tuple[Row, ...]] = {}
    for values in itertools.combinations(range(1, 17), 4):
        if sum(values) == MAGIC:
            mask = value_mask(values)
            row_masks[mask] = tuple(itertools.permutations(values))

    valid_masks = tuple(sorted(row_masks))
    valid_mask_set = set(valid_masks)
    disjoint = {
        mask: tuple(other for other in valid_masks if not mask & other)
        for mask in valid_masks
    }

    solutions: list[Grid] = []
    for mask0 in valid_masks:
        for mask1 in disjoint[mask0]:
            used01 = mask0 | mask1
            for mask2 in valid_masks:
                if used01 & mask2:
                    continue
                mask3 = FULL_MASK ^ (used01 | mask2)
                if mask3 not in valid_mask_set:
                    continue
                for row0 in row_masks[mask0]:
                    for row1 in row_masks[mask1]:
                        partial = tuple(row0[col] + row1[col] for col in range(N))
                        for row2 in row_masks[mask2]:
                            row3 = tuple(
                                MAGIC - partial[col] - row2[col] for col in range(N)
                            )
                            if value_mask(row3) != mask3:
                                continue
                            grid = row0 + row1 + row2 + row3
                            if (
                                grid[0] + grid[5] + grid[10] + grid[15] == MAGIC
                                and grid[3] + grid[6] + grid[9] + grid[12] == MAGIC
                            ):
                                solutions.append(grid)
    return solutions


def is_magic(grid: Grid) -> bool:
    if len(grid) != 16 or sorted(grid) != list(range(1, 17)):
        return False
    lines = [grid[i : i + 4] for i in range(0, 16, 4)]
    lines += [grid[col::4] for col in range(4)]
    lines += [
        (grid[0], grid[5], grid[10], grid[15]),
        (grid[3], grid[6], grid[9], grid[12]),
    ]
    return all(sum(line) == MAGIC for line in lines)


def rotate(grid: Grid) -> Grid:
    return tuple(
        grid[(N - 1 - col) * N + row]
        for row in range(N)
        for col in range(N)
    )


def reflect(grid: Grid) -> Grid:
    return tuple(
        grid[row * N + (N - 1 - col)]
        for row in range(N)
        for col in range(N)
    )


def d4_transforms(grid: Grid) -> tuple[Grid, ...]:
    images: list[Grid] = []
    current = grid
    for _ in range(4):
        images.extend((current, reflect(current)))
        current = rotate(current)
    return tuple(images)


def canonical(grid: Grid) -> Grid:
    return min(d4_transforms(grid))


def complement(grid: Grid) -> Grid:
    return tuple(COMPLEMENT - value for value in grid)


def is_associative(grid: Grid) -> bool:
    return all(
        grid[row * N + col]
        + grid[(N - 1 - row) * N + (N - 1 - col)]
        == COMPLEMENT
        for row in range(N)
        for col in range(N)
    )


def is_panmagic(grid: Grid) -> bool:
    for offset in range(N):
        if sum(grid[row * N + ((row + offset) % N)] for row in range(N)) != MAGIC:
            return False
        if sum(grid[row * N + ((offset - row) % N)] for row in range(N)) != MAGIC:
            return False
    return True


def is_most_perfect(grid: Grid) -> bool:
    toroidal_blocks = all(
        sum(
            grid[((row + dr) % N) * N + ((col + dc) % N)]
            for dr in range(2)
            for dc in range(2)
        )
        == MAGIC
        for row in range(N)
        for col in range(N)
    )
    half_diagonal_complements = all(
        grid[row * N + col]
        + grid[((row + N // 2) % N) * N + ((col + N // 2) % N)]
        == COMPLEMENT
        for row in range(N)
        for col in range(N)
    )
    return toroidal_blocks and half_diagonal_complements


def checksum(grids: list[Grid] | tuple[Grid, ...]) -> str:
    payload = "\n".join(",".join(map(str, grid)) for grid in sorted(grids)) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def analyze(grids: list[Grid], elapsed: float) -> dict[str, object]:
    oriented = set(grids)
    representatives = sorted({canonical(grid) for grid in oriented})
    orbit_histogram = Counter(len(set(d4_transforms(grid))) for grid in representatives)
    stabilizer_histogram = Counter(
        sum(image == grid for image in d4_transforms(grid))
        for grid in representatives
    )
    associative = {grid for grid in representatives if is_associative(grid)}
    panmagic = {grid for grid in representatives if is_panmagic(grid)}
    most_perfect = {grid for grid in representatives if is_most_perfect(grid)}
    complement_fixed = {
        grid
        for grid in representatives
        if canonical(complement(grid)) == grid
    }
    property_counts = {
        "associative": len(associative),
        "panmagic": len(panmagic),
        "most_perfect": len(most_perfect),
        "complement_fixed_mod_d4": len(complement_fixed),
        "associative_and_panmagic": len(associative & panmagic),
    }
    complement_orbits = {
        min(grid, canonical(complement(grid))) for grid in representatives
    }
    return {
        "algorithm": "sum-34 row masks; first three rows force fourth by columns",
        "enumeration_seconds": round(elapsed, 6),
        "oriented_count": len(grids),
        "unique_oriented_count": len(oriented),
        "d4_representative_count": len(representatives),
        "all_valid": all(is_magic(grid) for grid in oriented),
        "orbit_size_histogram": dict(sorted(orbit_histogram.items())),
        "stabilizer_size_histogram": dict(sorted(stabilizer_histogram.items())),
        "oriented_sha256": checksum(sorted(oriented)),
        "canonical_sha256": checksum(representatives),
        "property_counts_on_d4_representatives": property_counts,
        "panmagic_equals_most_perfect_at_order_4": panmagic == most_perfect,
        "complement_orbit_count_on_d4_representatives": len(complement_orbits),
        "counts_are_observed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    args = parser.parse_args()

    started = time.perf_counter()
    grids = enumerate_oriented()
    report = analyze(grids, time.perf_counter() - started)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
