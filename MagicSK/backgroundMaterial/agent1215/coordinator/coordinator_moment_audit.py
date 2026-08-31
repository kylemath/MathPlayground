#!/usr/bin/env python3
"""Verify a complete orthonormal 4x4 spatial basis and Parseval energy."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

Grid = tuple[int, ...]

P = (
    (1.0, 1.0, 1.0, 1.0),
    tuple(value / math.sqrt(5.0) for value in (-3.0, -1.0, 1.0, 3.0)),
    (1.0, -1.0, -1.0, 1.0),
    tuple(value / math.sqrt(5.0) for value in (-1.0, 3.0, -3.0, 1.0)),
)


def coefficient(grid: Grid, horizontal: int, vertical: int) -> float:
    return sum(
        (grid[row * 4 + column] - 8.5)
        * P[horizontal][column]
        * P[vertical][row]
        for row in range(4)
        for column in range(4)
    ) / 16.0


def coefficients(grid: Grid) -> dict[tuple[int, int], float]:
    return {
        (horizontal, vertical): coefficient(grid, horizontal, vertical)
        for vertical in range(4)
        for horizontal in range(4)
    }


def load(path: Path) -> list[Grid]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            tuple(int(row[f"cell_{index}"]) for index in range(1, 17))
            for row in csv.DictReader(handle)
        ]


def audit(path: Path) -> dict[str, object]:
    grids = load(path)
    gram_errors = [
        abs(
            sum(P[left][position] * P[right][position] for position in range(4))
            / 4.0
            - float(left == right)
        )
        for left in range(4)
        for right in range(4)
    ]
    parseval_errors: list[float] = []
    axis_coefficients: list[float] = []
    total_energies: list[float] = []
    residual_ranges: dict[str, list[float]] = {
        str(cutoff): [] for cutoff in range(2, 7)
    }

    for grid in grids:
        coeffs = coefficients(grid)
        spatial_energy = sum((value - 8.5) ** 2 for value in grid) / 16.0
        coefficient_energy = sum(value * value for value in coeffs.values())
        parseval_errors.append(abs(spatial_energy - coefficient_energy))
        total_energies.append(spatial_energy)
        axis_coefficients.extend(
            abs(value)
            for (horizontal, vertical), value in coeffs.items()
            if (horizontal == 0) != (vertical == 0)
        )
        for cutoff in range(2, 7):
            residual = sum(
                value * value
                for (horizontal, vertical), value in coeffs.items()
                if horizontal + vertical > cutoff
            )
            residual_ranges[str(cutoff)].append(residual / spatial_energy)

    return {
        "source": str(path.resolve()),
        "basis_values": P,
        "inner_product": "mean over four coordinate positions",
        "coefficient_inner_product": "mean over all 16 cells",
        "maximum_1d_gram_error": max(gram_errors),
        "maximum_parseval_error": max(parseval_errors),
        "maximum_magic_axis_mode_magnitude": max(axis_coefficients),
        "total_spatial_energy_range": [min(total_energies), max(total_energies)],
        "expected_permutation_energy": 21.25,
        "degree_cutoff_residual_fraction_ranges": {
            cutoff: [min(values), max(values)]
            for cutoff, values in residual_ranges.items()
        },
        "mode_order": [
            {
                "horizontal_degree": horizontal,
                "vertical_degree": vertical,
                "total_degree": horizontal + vertical,
            }
            for vertical in range(4)
            for horizontal in range(4)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.csv_path)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
