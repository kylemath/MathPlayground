#!/usr/bin/env python3
"""Standard-library verification of the 4x4 mean-weight moment specification."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

SIDE = 4
NCELLS = SIDE * SIDE
SQRT5 = math.sqrt(5.0)

# Degrees 0..3, evaluated from coordinate -3/2 to 3/2.  These vectors are
# orthonormal for <u,v>_1 = (1/4) sum_i u_i v_i.
PHI = (
    (1.0, 1.0, 1.0, 1.0),
    (-3.0 / SQRT5, -1.0 / SQRT5, 1.0 / SQRT5, 3.0 / SQRT5),
    (1.0, -1.0, -1.0, 1.0),
    (-1.0 / SQRT5, 3.0 / SQRT5, -3.0 / SQRT5, 1.0 / SQRT5),
)

MODES = tuple(
    (p, degree - p)
    for degree in range(7)
    for p in range(4)
    if 0 <= degree - p <= 3
)


def inner_1d(u: tuple[float, ...], v: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(u, v)) / SIDE


def basis_value(p: int, q: int, row: int, col: int) -> float:
    """p is column/x degree and q is row/y degree."""
    return PHI[p][col] * PHI[q][row]


def coefficients(grid: list[list[float]]) -> dict[tuple[int, int], float]:
    return {
        (p, q): sum(
            grid[row][col] * basis_value(p, q, row, col)
            for row in range(SIDE)
            for col in range(SIDE)
        )
        / NCELLS
        for p, q in MODES
    }


def reconstruct(coeff: dict[tuple[int, int], float]) -> list[list[float]]:
    return [
        [
            sum(coeff[p, q] * basis_value(p, q, row, col) for p, q in MODES)
            for col in range(SIDE)
        ]
        for row in range(SIDE)
    ]


def mean_square(grid: list[list[float]]) -> float:
    return sum(value * value for row in grid for value in row) / NCELLS


def max_abs(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def verify() -> dict[str, object]:
    gram_1d = [
        [inner_1d(PHI[p], PHI[q]) for q in range(SIDE)]
        for p in range(SIDE)
    ]
    gram_1d_error = max(
        abs(gram_1d[p][q] - (1.0 if p == q else 0.0))
        for p in range(SIDE)
        for q in range(SIDE)
    )

    flattened_modes = {
        mode: [
            basis_value(*mode, row, col)
            for row in range(SIDE)
            for col in range(SIDE)
        ]
        for mode in MODES
    }
    gram_2d_error = 0.0
    for a, mode_a in enumerate(MODES):
        for b, mode_b in enumerate(MODES):
            value = sum(
                x * y
                for x, y in zip(flattened_modes[mode_a], flattened_modes[mode_b])
            ) / NCELLS
            target = 1.0 if a == b else 0.0
            gram_2d_error = max(gram_2d_error, abs(value - target))

    rng = random.Random(1215)
    test_grid = [
        [rng.uniform(-20.0, 20.0) for _ in range(SIDE)] for _ in range(SIDE)
    ]
    test_coeff = coefficients(test_grid)
    test_reconstruction = reconstruct(test_coeff)
    reconstruction_error = max(
        abs(test_grid[row][col] - test_reconstruction[row][col])
        for row in range(SIDE)
        for col in range(SIDE)
    )
    parseval_error = abs(
        mean_square(test_grid) - sum(value * value for value in test_coeff.values())
    )

    durer = [
        [16.0, 3.0, 2.0, 13.0],
        [5.0, 10.0, 11.0, 8.0],
        [9.0, 6.0, 7.0, 12.0],
        [4.0, 15.0, 14.0, 1.0],
    ]
    mean = sum(value for row in durer for value in row) / NCELLS
    centered = [[value - mean for value in row] for row in durer]
    magic_coeff = coefficients(centered)
    axis_modes = ((1, 0), (2, 0), (3, 0), (0, 1), (0, 2), (0, 3))
    axis_error = max_abs([magic_coeff[mode] for mode in axis_modes])
    main_diagonal_relation = sum(magic_coeff[p, p] for p in range(1, 4))
    anti_diagonal_relation = sum(
        ((-1.0) ** p) * magic_coeff[p, p] for p in range(1, 4)
    )
    c22_error = abs(magic_coeff[2, 2])
    c33_plus_c11_error = abs(magic_coeff[3, 3] + magic_coeff[1, 1])
    nonconstant_energy = sum(
        value * value for mode, value in magic_coeff.items() if mode != (0, 0)
    )

    expected_variance = 255.0 / 12.0
    checks = {
        "mode_count": len(MODES),
        "gram_1d_max_abs_error": gram_1d_error,
        "gram_2d_max_abs_error": gram_2d_error,
        "reconstruction_max_abs_error": reconstruction_error,
        "parseval_abs_error": parseval_error,
        "magic_axis_max_abs": axis_error,
        "magic_main_diagonal_relation_abs": abs(main_diagonal_relation),
        "magic_anti_diagonal_relation_abs": abs(anti_diagonal_relation),
        "magic_c22_abs": c22_error,
        "magic_c33_plus_c11_abs": c33_plus_c11_error,
        "magic_nonconstant_energy": nonconstant_energy,
        "expected_permutation_variance": expected_variance,
        "variance_abs_error": abs(nonconstant_energy - expected_variance),
    }
    tolerances = {
        "orthogonality": 1e-12,
        "reconstruction": 1e-12,
        "parseval": 1e-12,
        "constraint_zero": 1e-10,
    }
    passed = (
        len(MODES) == 16
        and gram_1d_error < tolerances["orthogonality"]
        and gram_2d_error < tolerances["orthogonality"]
        and reconstruction_error < tolerances["reconstruction"]
        and parseval_error < tolerances["parseval"]
        and axis_error < tolerances["constraint_zero"]
        and abs(main_diagonal_relation) < tolerances["constraint_zero"]
        and abs(anti_diagonal_relation) < tolerances["constraint_zero"]
        and c22_error < tolerances["constraint_zero"]
        and c33_plus_c11_error < tolerances["constraint_zero"]
        and abs(nonconstant_energy - expected_variance) < tolerances["parseval"]
    )
    return {
        "passed": passed,
        "normalization": "mean-weight inner products (1/4 in 1D, 1/16 in 2D)",
        "mode_order": [list(mode) for mode in MODES],
        "tolerances": tolerances,
        "checks": checks,
    }


def main() -> None:
    result = verify()
    text = json.dumps(result, indent=2) + "\n"
    print(text, end="")
    output_path = Path(__file__).with_name("manager_verification_output.json")
    output_path.write_text(text, encoding="utf-8")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
