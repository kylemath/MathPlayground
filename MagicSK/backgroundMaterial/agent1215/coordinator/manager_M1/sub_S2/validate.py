"""Validation of normal order-4 magic squares."""

from __future__ import annotations

Grid = tuple[int, ...]

ORDER = 4
MAGIC_CONSTANT = 34  # n(n^2 + 1) / 2 for n = 4
EXPECTED_VALUES = tuple(range(1, ORDER * ORDER + 1))


def rows(grid: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(grid[r * ORDER : (r + 1) * ORDER] for r in range(ORDER))


def columns(grid: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(grid[c::ORDER]) for c in range(ORDER))


def diagonals(grid: Grid) -> tuple[tuple[int, ...], tuple[int, ...]]:
    main = (grid[0], grid[5], grid[10], grid[15])
    anti = (grid[3], grid[6], grid[9], grid[12])
    return main, anti


def line_sums(grid: Grid) -> tuple[int, ...]:
    sums: list[int] = []
    for line in (*rows(grid), *columns(grid), *diagonals(grid)):
        sums.append(sum(line))
    return tuple(sums)


def is_normal(grid: Grid) -> bool:
    """Uses each value 1..16 exactly once."""
    return len(grid) == ORDER * ORDER and sorted(grid) == list(EXPECTED_VALUES)


def is_magic(grid: Grid) -> bool:
    """Normal square with all rows, columns, and diagonals summing to 34."""
    return is_normal(grid) and all(total == MAGIC_CONSTANT for total in line_sums(grid))


def validate(grid: Grid) -> dict[str, object]:
    """Structured validation report for one grid."""
    return {
        "normal": is_normal(grid),
        "magic": is_magic(grid),
        "magic_constant": MAGIC_CONSTANT,
        "line_sums": line_sums(grid),
        "line_sums_uniform": len(set(line_sums(grid))) == 1 if is_normal(grid) else False,
    }
