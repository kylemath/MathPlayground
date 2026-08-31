"""D4 (dihedral group of the square) transforms for 4x4 grids.

D4 has 8 elements: 4 rotations and 4 reflections (rotation then horizontal flip).
Complement (17 - x) is NOT part of D4.
"""

from __future__ import annotations

Grid = tuple[int, ...]

ORDER = 4
CELL_COUNT = ORDER * ORDER


def _index(row: int, col: int) -> int:
    return row * ORDER + col


def rotate_clockwise(grid: Grid) -> Grid:
    """90-degree clockwise rotation."""
    return tuple(
        grid[_index(ORDER - 1 - col, row)]
        for row in range(ORDER)
        for col in range(ORDER)
    )


def reflect_vertical_axis(grid: Grid) -> Grid:
    """Reflection across the vertical midline (left <-> right)."""
    return tuple(
        grid[_index(row, ORDER - 1 - col)]
        for row in range(ORDER)
        for col in range(ORDER)
    )


def d4_transforms(grid: Grid) -> tuple[Grid, ...]:
    """Return all 8 D4 images in deterministic generation order."""
    images: list[Grid] = []
    current = grid
    for _ in range(4):
        images.append(current)
        images.append(reflect_vertical_axis(current))
        current = rotate_clockwise(current)
    return tuple(images)


def d4_orbit(grid: Grid) -> frozenset[Grid]:
    """Distinct D4 images (orbit); duplicates only if grid has D4 symmetry."""
    return frozenset(d4_transforms(grid))


def canonical(grid: Grid) -> Grid:
    """Lexicographic minimum over the D4 orbit."""
    return min(d4_orbit(grid))


def orbit_size(grid: Grid) -> int:
    return len(d4_orbit(grid))


def stabilizer_size(grid: Grid) -> int:
    """|Stab_{D4}(grid)| = 8 / |orbit|."""
    size = orbit_size(grid)
    if 8 % size != 0:
        raise ValueError(f"orbit size {size} does not divide 8")
    return 8 // size


def is_d4_canonical(grid: Grid) -> bool:
    return grid == canonical(grid)
