"""Deterministic enumeration of normal 4x4 magic squares via sum-34 row masks.

Algorithm (standard library only):
1. Precompute the 86 four-element subsets of {1..16} whose entries sum to 34.
2. For each ordered triple of disjoint row masks, permute the first three rows.
3. Derive the fourth row from column-sum constraints (each column sums to 34).
4. Keep candidates whose fourth row is a valid sum-34 mask and whose diagonals sum to 34.

This yields all 7,040 oriented squares deterministically without slow backtracking.
"""

from __future__ import annotations

import itertools

from validate import MAGIC_CONSTANT, ORDER

Grid = tuple[int, ...]
Row = tuple[int, ...]

FULL_MASK = (1 << 16) - 1


def value_mask(values: tuple[int, ...]) -> int:
    """Bit mask for values in 1..16; returns -1 on duplicate or out-of-range."""
    mask = 0
    for value in values:
        if not 1 <= value <= 16:
            return -1
        bit = 1 << (value - 1)
        if mask & bit:
            return -1
        mask |= bit
    return mask


def _build_row_masks() -> tuple[dict[int, tuple[Row, ...]], tuple[int, ...], set[int]]:
    row_masks: dict[int, tuple[Row, ...]] = {}
    for values in itertools.combinations(range(1, 17), 4):
        if sum(values) == MAGIC_CONSTANT:
            mask = value_mask(values)
            row_masks[mask] = tuple(itertools.permutations(values))
    valid_masks = tuple(sorted(row_masks))
    return row_masks, valid_masks, set(valid_masks)


_ROW_MASKS, _VALID_MASKS, _VALID_MASK_SET = _build_row_masks()
_DISJOINT = {
    mask: tuple(other for other in _VALID_MASKS if not mask & other)
    for mask in _VALID_MASKS
}


def row_mask_count() -> int:
    """Number of four-value subsets summing to the magic constant."""
    return len(_VALID_MASKS)


def enumerate_oriented_magic_squares() -> tuple[Grid, ...]:
    """Return all oriented normal order-4 magic squares in deterministic order."""
    solutions: list[Grid] = []

    for mask0 in _VALID_MASKS:
        for mask1 in _DISJOINT[mask0]:
            used01 = mask0 | mask1
            for mask2 in _VALID_MASKS:
                if used01 & mask2:
                    continue
                mask3 = FULL_MASK ^ (used01 | mask2)
                if mask3 not in _VALID_MASK_SET:
                    continue
                for row0 in _ROW_MASKS[mask0]:
                    for row1 in _ROW_MASKS[mask1]:
                        partial = tuple(row0[col] + row1[col] for col in range(ORDER))
                        for row2 in _ROW_MASKS[mask2]:
                            row3 = tuple(
                                MAGIC_CONSTANT - partial[col] - row2[col]
                                for col in range(ORDER)
                            )
                            if value_mask(row3) != mask3:
                                continue
                            grid = row0 + row1 + row2 + row3
                            if (
                                grid[0] + grid[5] + grid[10] + grid[15] == MAGIC_CONSTANT
                                and grid[3] + grid[6] + grid[9] + grid[12] == MAGIC_CONSTANT
                            ):
                                solutions.append(grid)

    return tuple(solutions)


def enumerate_d4_representatives() -> tuple[Grid, ...]:
    """Lex-min D4 canonical representatives derived from oriented enumeration."""
    from d4 import canonical

    return tuple(sorted({canonical(grid) for grid in enumerate_oriented_magic_squares()}))
