#!/usr/bin/env python3
"""Structural classification and reproduced count checks for normal order-4 magic squares.

Standard library only. Can enumerate from scratch or audit an external CSV of 880 D4 representatives.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

N = 4
MAGIC_SUM = 34
COMPLEMENT_SUM = 17
Grid = tuple[int, ...]

# ---------------------------------------------------------------------------
# Geometry: D4 action on flat row-major grids
# ---------------------------------------------------------------------------


def to_matrix(grid: Grid) -> list[list[int]]:
    return [list(grid[offset : offset + N]) for offset in range(0, N * N, N)]


def from_matrix(matrix: list[list[int]]) -> Grid:
    return tuple(value for row in matrix for value in row)


def rotate_clockwise(grid: Grid) -> Grid:
    matrix = to_matrix(grid)
    rotated = [list(row) for row in zip(*matrix[::-1])]
    return from_matrix(rotated)


def reflect_left_right(grid: Grid) -> Grid:
    return tuple(grid[row * N + (N - 1 - column)] for row in range(N) for column in range(N))


def d4_images(grid: Grid) -> set[Grid]:
    images: set[Grid] = set()
    current = grid
    for _ in range(4):
        images.add(current)
        images.add(reflect_left_right(current))
        current = rotate_clockwise(current)
    return images


def d4_canonical(grid: Grid) -> Grid:
    """Lexicographic minimum over the eight D4 images (Frénicle-style representative)."""
    return min(d4_images(grid))


def complement(grid: Grid) -> Grid:
    """Entrywise complement x -> (n^2 + 1) - x for normal order n."""
    return tuple(COMPLEMENT_SUM - value for value in grid)


def rotate_180(grid: Grid) -> Grid:
    return rotate_clockwise(rotate_clockwise(grid))


def complement_commutes_with_d4(grid: Grid) -> bool:
    """Check complement(g·S) = g·complement(S) for all eight D4 images."""
    return all(
        complement(image) in d4_images(complement(grid))
        for image in d4_images(grid)
    )


# ---------------------------------------------------------------------------
# Line-sum utilities
# ---------------------------------------------------------------------------


def rows(grid: Grid) -> list[tuple[int, ...]]:
    return [grid[offset : offset + N] for offset in range(0, N * N, N)]


def columns(grid: Grid) -> list[tuple[int, ...]]:
    return [tuple(grid[column::N]) for column in range(N)]


def main_diagonals(grid: Grid) -> tuple[tuple[int, ...], tuple[int, ...]]:
    matrix = to_matrix(grid)
    return (
        tuple(matrix[index][index] for index in range(N)),
        tuple(matrix[index][N - 1 - index] for index in range(N)),
    )


def broken_diagonals(grid: Grid) -> list[tuple[int, ...]]:
    """All length-n wrap-around diagonals in both directions (8 total for n=4)."""
    matrix = to_matrix(grid)
    lines: list[tuple[int, ...]] = []
    for offset in range(N):
        lines.append(tuple(matrix[row][(row + offset) % N] for row in range(N)))
        lines.append(tuple(matrix[row][(offset - row) % N] for row in range(N)))
    return lines


def opposite_short_diagonals(grid: Grid) -> list[tuple[int, ...]]:
    """Pairs of opposite 2-cell diagonals (Dudeney semi-Nasik / bent-diagonal tests)."""
    matrix = to_matrix(grid)
    return [
        (matrix[0][0], matrix[1][1], matrix[2][3], matrix[3][2]),
        (matrix[0][3], matrix[1][2], matrix[2][1], matrix[3][0]),
        (matrix[0][1], matrix[1][0], matrix[2][2], matrix[3][3]),
        (matrix[0][2], matrix[1][3], matrix[2][0], matrix[3][1]),
    ]


def line_sum(line: Iterable[int]) -> int:
    return sum(line)


# ---------------------------------------------------------------------------
# Property predicates (explicit, non-conflated)
# ---------------------------------------------------------------------------


def is_normal(grid: Grid) -> bool:
    return sorted(grid) == list(range(1, N * N + 1))


def is_magic(grid: Grid) -> bool:
    if not is_normal(grid):
        return False
    row_sums = [line_sum(row) for row in rows(grid)]
    column_sums = [line_sum(column) for column in columns(grid)]
    diag_sums = [line_sum(diagonal) for diagonal in main_diagonals(grid)]
    return all(value == MAGIC_SUM for value in row_sums + column_sums + diag_sums)


def is_pandiagonal(grid: Grid) -> bool:
    """Panmagic / Nasik / pandiagonal: all broken diagonals also sum to the magic constant."""
    return is_magic(grid) and all(line_sum(line) == MAGIC_SUM for line in broken_diagonals(grid))


def is_frenicle_standard(grid: Grid) -> bool:
    """Frénicle / D4-lex tie-break used for 880 representatives (see Wikipedia, Heinz)."""
    matrix = to_matrix(grid)
    corners = (matrix[0][0], matrix[0][3], matrix[3][0], matrix[3][3])
    if matrix[0][0] != min(corners):
        return False
    return matrix[0][1] < matrix[1][0]


def broken_diagonal_magic_count(grid: Grid) -> int:
    return sum(line_sum(line) == MAGIC_SUM for line in broken_diagonals(grid))


def is_bent_semi_pandiagonal(grid: Grid) -> bool:
    """Dudeney Type II bent-diagonal property: four opposite short diagonals each sum to 34."""
    return is_magic(grid) and all(line_sum(line) == MAGIC_SUM for line in opposite_short_diagonals(grid))


def is_semi_pandiagonal(grid: Grid) -> bool:
    """Alias for bent-diagonal semi-pandiagonal (strict geometric test, 48 squares)."""
    return is_bent_semi_pandiagonal(grid)


def is_associative(grid: Grid) -> bool:
    """Center-symmetric complementary pairs: a[r,c] + a[n-1-r,n-1-c] = n^2 + 1."""
    matrix = to_matrix(grid)
    return all(
        matrix[row][column] + matrix[N - 1 - row][N - 1 - column] == COMPLEMENT_SUM
        for row in range(N)
        for column in range(N)
    )


def is_most_perfect(grid: Grid) -> bool:
    """Ollerenshaw–Bree most-perfect (order 4): all 2x2 toroidal blocks sum to 34 and
    cells two steps apart on diagonals are complementary (sum 17)."""
    matrix = to_matrix(grid)
    toroidal_2x2 = all(
        sum(
            matrix[(row + dy) % N][(column + dx) % N]
            for dy in range(2)
            for dx in range(2)
        )
        == MAGIC_SUM
        for row in range(N)
        for column in range(N)
    )
    diagonal_complements = all(
        matrix[row][column] + matrix[(row + 2) % N][(column + 2) % N] == COMPLEMENT_SUM
        for row in range(N)
        for column in range(N)
    )
    return is_magic(grid) and toroidal_2x2 and diagonal_complements


def is_self_complementary(grid: Grid) -> bool:
    """Fixed setwise under complement (may differ by D4 symmetry)."""
    return d4_canonical(complement(grid)) == d4_canonical(grid)


def compact_2x2_blocks(grid: Grid) -> bool:
    """Non-toroidal compact: all nine contiguous 2×2 windows in the 4×4 grid sum to 34.

    Distinct from most-perfect, which requires all sixteen 2×2 toroidal (wrap-around) windows.
    """
    matrix = to_matrix(grid)
    return all(
        sum(
            matrix[row + dy][column + dx]
            for dy in range(2)
            for dx in range(2)
        )
        == MAGIC_SUM
        for row in range(N - 1)
        for column in range(N - 1)
    )


def classify(grid: Grid) -> dict[str, bool | int]:
    return {
        "magic": is_magic(grid),
        "pandiagonal": is_pandiagonal(grid),
        "bent_semi_pandiagonal": is_bent_semi_pandiagonal(grid),
        "associative": is_associative(grid),
        "most_perfect": is_most_perfect(grid),
        "self_complementary": is_self_complementary(grid),
        "compact_2x2": compact_2x2_blocks(grid),
        "frenicle_standard": is_frenicle_standard(grid),
        "broken_diagonal_magic_count": broken_diagonal_magic_count(grid),
    }


# ---------------------------------------------------------------------------
# Enumeration (independent reproduction of 880 / 7040)
# ---------------------------------------------------------------------------


def _row_complete_ok(cells: list[int | None], row_index: int) -> bool:
    start = row_index * N
    row = cells[start : start + N]
    if any(value is None for value in row):
        return True
    return line_sum(value for value in row if value is not None) == MAGIC_SUM  # type: ignore[arg-type]


def _column_complete_ok(cells: list[int | None], column_index: int) -> bool:
    column = [cells[row * N + column_index] for row in range(N)]
    if any(value is None for value in column):
        return True
    return line_sum(value for value in column if value is not None) == MAGIC_SUM  # type: ignore[arg-type]


def enumerate_oriented_magic() -> list[Grid]:
    """Enumerate all oriented normal order-4 magic squares via backtracking."""
    results: list[Grid] = []
    cells: list[int | None] = [None] * (N * N)
    used = [False] * (N * N + 1)

    def search(index: int) -> None:
        if index == N * N:
            grid = tuple(value for value in cells)  # type: ignore[misc]
            if is_magic(grid):
                results.append(grid)
            return

        row, column = divmod(index, N)
        for value in range(1, N * N + 1):
            if used[value]:
                continue
            cells[index] = value
            used[value] = True
            if _row_complete_ok(cells, row) and _column_complete_ok(cells, column):
                search(index + 1)
            cells[index] = None
            used[value] = False

    search(0)
    return results


def count_report(grids: Iterable[Grid], *, assume_frenicle_representatives: bool = False) -> dict[str, object]:
    grids = list(grids)
    if assume_frenicle_representatives:
        canonicals = set(grids)
        oriented = {image for grid in grids for image in d4_images(grid)}
    else:
        canonicals = {d4_canonical(grid) for grid in grids}
        oriented = set(grids)

    orbit_sizes = Counter(len(d4_images(grid)) for grid in canonicals)
    property_counts: Counter[str] = Counter()
    broken_diagonal_histogram: Counter[int] = Counter()
    for grid in canonicals:
        props = classify(grid)
        for name, value in props.items():
            if name == "broken_diagonal_magic_count":
                broken_diagonal_histogram[int(value)] += 1
            elif value:
                property_counts[name] += 1

    complement_pairs: Counter[tuple[Grid, Grid]] = Counter()
    for grid in canonicals:
        pair = tuple(sorted((grid, d4_canonical(complement(grid)))))
        complement_pairs[pair] += 1

    fixed_points = sum(1 for count in complement_pairs.values() if count == 1)
    two_cycles = sum(1 for count in complement_pairs.values() if count == 2)

    return {
        "oriented_count": len(oriented),
        "d4_canonical_count": len(canonicals),
        "d4_orbit_size_distribution": dict(sorted(orbit_sizes.items())),
        "property_counts_on_d4_canonicals": dict(sorted(property_counts.items())),
        "broken_diagonal_count_histogram": dict(sorted(broken_diagonal_histogram.items())),
        "self_complementary_d4_canonicals": property_counts["self_complementary"],
        "complement_orbit_total": len(complement_pairs),
        "complement_orbit_fixed_points": fixed_points,
        "complement_orbit_two_cycles": two_cycles,
        "complement_pair_orbit_count": len(complement_pairs),
        "complement_pairs_of_size_1": fixed_points,
        "complement_pairs_of_size_2": two_cycles,
    }


def expand_oriented_from_csv(path: Path) -> dict[str, object]:
    """Derive 7040 oriented squares by D4-expansion of 880 CSV representatives."""
    with path.open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    grids = [
        tuple(int(row[f"cell_{index}"]) for index in range(1, 17))
        for row in records
    ]
    oriented = {image for grid in grids for image in d4_images(grid)}
    frenicle_ok = sum(is_frenicle_standard(grid) for grid in grids)
    return {
        "csv_records": len(grids),
        "expanded_oriented_count": len(oriented),
        "all_records_frenicle_standard": frenicle_ok == len(grids),
        "all_orbit_sizes_8": all(len(d4_images(grid)) == 8 for grid in grids),
        "expected_oriented_if_all_orbits_8": len(grids) * 8,
    }


def audit_csv(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))

    grids = [
        tuple(int(row[f"cell_{index}"]) for index in range(1, 17))
        for row in records
    ]
    canonical_report = count_report(grids)
    dudeney = Counter(int(row["dudeney_group"]) for row in records)

    # Cross-check structural labels against Dudeney metadata where applicable.
    mismatches: list[dict[str, object]] = []
    for row, grid in zip(records, grids):
        props = classify(grid)
        group = int(row["dudeney_group"])
        if group == 1 and not props["pandiagonal"]:
            mismatches.append({"id": row["id"], "issue": "group I not pandiagonal"})
        if group == 3 and not props["associative"]:
            mismatches.append({"id": row["id"], "issue": "group III not associative"})
        if props["pandiagonal"] and props["associative"]:
            mismatches.append({"id": row["id"], "issue": "both pandiagonal and associative"})

    transform_checks = {
        "complement_commutes_with_d4_all_records": all(
            complement_commutes_with_d4(grid) for grid in grids
        ),
        "complement_preserves_associative_all_records": all(
            is_associative(grid) == is_associative(complement(grid)) for grid in grids
        ),
        "associative_implies_complement_is_rotate180": all(
            complement(grid) in d4_images(rotate_180(grid))
            for grid in grids
            if is_associative(grid)
        ),
    }

    return {
        "source_csv": str(path.resolve()),
        "record_count": len(records),
        "dudeney_group_distribution": dict(sorted(dudeney.items())),
        "dudeney_label_mismatches": mismatches,
        "d4_expansion": expand_oriented_from_csv(path),
        "transform_identity_checks": transform_checks,
        **canonical_report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        help="Optional CSV of 880 D4 representatives (e.g. Heinz/Frénicle list)",
    )
    parser.add_argument(
        "--enumerate",
        action="store_true",
        help="Independently enumerate all oriented squares (slow but self-contained)",
    )
    parser.add_argument("--output", type=Path, help="Write JSON results here")
    args = parser.parse_args()

    results: dict[str, object] = {}

    if args.enumerate:
        oriented = enumerate_oriented_magic()
        results["enumeration"] = count_report(oriented, assume_frenicle_representatives=False)

    if args.csv:
        results["csv_audit"] = audit_csv(args.csv)

    if not results:
        parser.error("Provide --enumerate and/or --csv")

    rendered = json.dumps(results, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
