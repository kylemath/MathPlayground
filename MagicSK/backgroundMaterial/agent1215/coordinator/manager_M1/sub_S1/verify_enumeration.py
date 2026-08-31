#!/usr/bin/env python3
"""Independent oriented enumeration via 7-parameter closed-form solve."""

from __future__ import annotations

import json
from collections import Counter
from itertools import permutations
from pathlib import Path

MAGIC = 34
FREE = (0, 1, 2, 4, 5, 6, 8)
Grid = tuple[int, ...]


def solve_from_free(values: tuple[int, ...]) -> Grid | None:
    g = [0] * 16
    for index, value in zip(FREE, values):
        g[index] = value

    g[3] = MAGIC - g[0] - g[1] - g[2]
    g[7] = MAGIC - g[4] - g[5] - g[6]
    g[12] = MAGIC - g[0] - g[4] - g[8]
    g[9] = MAGIC - g[3] - g[6] - g[12]
    g[13] = MAGIC - g[1] - g[5] - g[9]

    # x10 from main-diagonal and row-4 relations (half-integer guard below)
    numerator = MAGIC - g[0] - g[5] - g[2] - g[6] + g[12] + g[13]
    if numerator % 2 != 0:
        return None
    g[10] = numerator // 2

    g[15] = MAGIC - g[0] - g[5] - g[10]
    g[11] = MAGIC - g[3] - g[7] - g[15]
    g[14] = MAGIC - g[2] - g[6] - g[10]

    if any(x < 1 or x > 16 for x in g):
        return None
    if len(set(g)) != 16:
        return None
    return tuple(g)


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


def canonical_lex(grid: Grid) -> Grid:
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


def enumerate_oriented() -> list[Grid]:
    squares: list[Grid] = []
    for perm in permutations(range(1, 17), 7):
        grid = solve_from_free(perm)
        if grid is None:
            continue
        if is_magic(grid):
            squares.append(grid)
    return squares


def main() -> None:
    squares = enumerate_oriented()
    canonical = {canonical_lex(g) for g in squares}
    stabilizers = Counter(stabilizer_size(g) for g in squares)
    orbits = Counter(len(d4_images(rep)) for rep in canonical)
    summary = {
        "method": "7-free-parameter linear basis; P(16,7) assignments",
        "oriented_count": len(squares),
        "unique_oriented": len(set(squares)),
        "d4_canonical_lex_count": len(canonical),
        "stabilizer_histogram": dict(sorted(stabilizers.items())),
        "orbit_size_histogram_on_canonical_reps": dict(sorted(orbits.items())),
        "all_stabilizers_trivial": stabilizers.get(1, 0) == len(squares),
        "product_check_canonical_times_8": len(canonical) * 8 == len(squares),
    }
    out = Path(__file__).with_name("verify_enumeration_results.json")
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
