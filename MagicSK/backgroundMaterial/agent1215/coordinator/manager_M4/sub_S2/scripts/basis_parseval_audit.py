#!/usr/bin/env python3
"""Independent audit: 1D basis orthonormality, 2D completeness, Parseval, reconstruction."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

N = 4
MEAN_HEIGHT = 8.5
TOTAL_HEIGHT_ENERGY = 340.0
COORDINATES = (-1.5, -0.5, 0.5, 1.5)
PROJECT_ROOT = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer")
ANALYSIS_JSON = PROJECT_ROOT / "data" / "analysis.json"


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def orthonormal_polynomials() -> list[list[float]]:
    basis: list[list[float]] = []
    for degree in range(N):
        vector = [coordinate**degree for coordinate in COORDINATES]
        for previous in basis:
            projection = dot(vector, previous)
            vector = [value - projection * prior for value, prior in zip(vector, previous)]
        norm = math.sqrt(dot(vector, vector))
        basis.append([value / norm for value in vector])
    return basis


def matrix(cells: list[int]) -> list[list[int]]:
    return [cells[offset : offset + N] for offset in range(0, N * N, N)]


def coefficient(
    heights: list[list[float]], x_degree: int, y_degree: int, basis: list[list[float]]
) -> float:
    return sum(
        basis[x_degree][column] * basis[y_degree][row] * heights[row][column]
        for row in range(N)
        for column in range(N)
    )


def reconstruct(
    coefficients: dict[tuple[int, int], float], basis: list[list[float]]
) -> list[list[float]]:
    grid = [[0.0 for _ in range(N)] for _ in range(N)]
    for row in range(N):
        for column in range(N):
            grid[row][column] = sum(
                coefficients[(x_degree, y_degree)]
                * basis[x_degree][column]
                * basis[y_degree][row]
                for x_degree in range(N)
                for y_degree in range(N)
            )
    return grid


def gram_matrix(basis: list[list[float]]) -> list[list[float]]:
    return [[dot(basis[i], basis[j]) for j in range(N)] for i in range(N)]


def tensor_gram(basis: list[list[float]]) -> list[list[float]]:
    size = N * N
    flat: list[list[float]] = []
    for y_degree in range(N):
        for x_degree in range(N):
            flat.append(
                [
                    basis[x_degree][column] * basis[y_degree][row]
                    for row in range(N)
                    for column in range(N)
                ]
            )
    return [[dot(flat[i], flat[j]) for j in range(size)] for i in range(size)]


def mode_name(x_degree: int, y_degree: int) -> str:
    return f"M{x_degree}{y_degree}"


def audit_basis() -> dict:
    basis = orthonormal_polynomials()
    gram_1d = gram_matrix(basis)
    gram_2d = tensor_gram(basis)

    orthonormal_1d = all(
        abs(gram_1d[i][j] - (1.0 if i == j else 0.0)) < 1e-12
        for i in range(N)
        for j in range(N)
    )
    orthonormal_2d = all(
        abs(gram_2d[i][j] - (1.0 if i == j else 0.0)) < 1e-12
        for i in range(N * N)
        for j in range(N * N)
    )

    with ANALYSIS_JSON.open(encoding="utf-8") as handle:
        shipped_basis = json.load(handle)["metadata"]["basis"]

    basis_matches_shipped = all(
        abs(recomputed - shipped) < 1e-9
        for recomputed, shipped in zip(
            (round(value, 10) for row in basis for value in row),
            (value for row in shipped_basis for value in row),
        )
    )

    return {
        "coordinates": COORDINATES,
        "basis_1d": basis,
        "gram_1d": gram_1d,
        "orthonormal_1d": orthonormal_1d,
        "orthonormal_2d_tensor": orthonormal_2d,
        "basis_matches_analysis_json": basis_matches_shipped,
        "max_1d_gram_error": max(
            abs(gram_1d[i][j] - (1.0 if i == j else 0.0))
            for i in range(N)
            for j in range(N)
        ),
    }


def audit_record(record: dict, basis: list[list[float]]) -> dict:
    cells = record["cells"]
    heights = [[value - MEAN_HEIGHT for value in row] for row in matrix(cells)]

    coefficients = {
        (x_degree, y_degree): coefficient(heights, x_degree, y_degree, basis)
        for x_degree in range(N)
        for y_degree in range(N)
    }

    height_energy = sum(value * value for row in heights for value in row)
    coeff_energy = sum(value * value for value in coefficients.values())
    parseval_ok = abs(height_energy - coeff_energy) < 1e-9

    reconstructed = reconstruct(coefficients, basis)
    max_recon_error = max(
        abs(reconstructed[row][column] - heights[row][column])
        for row in range(N)
        for column in range(N)
    )

    shipped_mode_energy = sum(record["modeEnergy"].values())
    shipped_axial = record["axialEnergy"]
    shipped_interaction = record["interactionEnergy"]
    m00 = coefficients[(0, 0)]
    m00_energy = m00 * m00

    recomputed_axial = sum(
        coefficients[(x_degree, y_degree)] ** 2
        for x_degree in range(N)
        for y_degree in range(N)
        if (x_degree == 0) != (y_degree == 0)
    )
    recomputed_interaction = sum(
        coefficients[(x_degree, y_degree)] ** 2
        for x_degree in range(1, N)
        for y_degree in range(1, N)
    )

    coeff_matches = all(
        abs(coefficients[(int(name[1]), int(name[2]))] - record["coefficients"][name]) < 1e-6
        for name in record["coefficients"]
    )

    return {
        "recordId": record["recordId"],
        "height_energy": height_energy,
        "coeff_energy": coeff_energy,
        "parseval_ok": parseval_ok,
        "max_reconstruction_error": max_recon_error,
        "m00_coefficient": m00,
        "m00_energy": m00_energy,
        "shipped_mode_energy_sum": shipped_mode_energy,
        "shipped_axial": shipped_axial,
        "recomputed_axial": recomputed_axial,
        "shipped_interaction": shipped_interaction,
        "recomputed_interaction": recomputed_interaction,
        "coeff_matches_shipped": coeff_matches,
        "axial_plus_interaction_plus_m00": recomputed_axial + recomputed_interaction + m00_energy,
    }


def audit_magic_axial_zero(records: list[dict]) -> dict:
    magic = [record for record in records if record["cohort"] == "magic"]
    nonzero_axial = [record["recordId"] for record in magic if record["axialEnergy"] != 0.0]
    return {
        "magic_count": len(magic),
        "nonzero_axial_count": len(nonzero_axial),
        "all_magic_axial_zero": len(nonzero_axial) == 0,
        "sample_nonzero": nonzero_axial[:5],
    }


def main() -> int:
    basis_report = audit_basis()
    with ANALYSIS_JSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    sample_ids = ["M001", "M042", "M880", "R001", "R880", "S1-001", "S2-042", "S3-880"]
    records_by_id = {record["recordId"]: record for record in payload["records"]}
    record_reports = [audit_record(records_by_id[record_id], basis_report["basis_1d"]) for record_id in sample_ids]
    magic_axial = audit_magic_axial_zero(payload["records"])

    constant_height_energy = {
        record_id: audit_record(records_by_id[record_id], basis_report["basis_1d"])["height_energy"]
        for record_id in sample_ids
    }

    report = {
        "basis": basis_report,
        "height_energy_constant_340": all(abs(value - TOTAL_HEIGHT_ENERGY) < 1e-9 for value in constant_height_energy.values()),
        "sample_height_energies": constant_height_energy,
        "sample_records": record_reports,
        "magic_axial_audit": magic_axial,
        "metadata_height_energy": payload["metadata"]["heightEnergy"],
    }

    out_dir = Path(__file__).resolve().parents[1] / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "basis_parseval_audit.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== Basis / Parseval / Reconstruction Audit ===")
    print(f"1D orthonormal: {basis_report['orthonormal_1d']} (max err {basis_report['max_1d_gram_error']:.3e})")
    print(f"2D tensor orthonormal: {basis_report['orthonormal_2d_tensor']}")
    print(f"Basis matches analysis.json: {basis_report['basis_matches_analysis_json']}")
    print(f"Height energy constant 340: {report['height_energy_constant_340']}")
    print(f"Magic axial all zero: {magic_axial['all_magic_axial_zero']} ({magic_axial['magic_count']} records)")
    for item in record_reports:
        print(
            f"{item['recordId']}: parseval={item['parseval_ok']}, "
            f"recon_err={item['max_reconstruction_error']:.3e}, "
            f"coeff_match={item['coeff_matches_shipped']}, "
            f"axial={item['shipped_axial']:.8f}"
        )
    print(f"Wrote {json_path}")
    return 0 if all(
        [
            basis_report["orthonormal_1d"],
            basis_report["orthonormal_2d_tensor"],
            basis_report["basis_matches_analysis_json"],
            report["height_energy_constant_340"],
            magic_axial["all_magic_axial_zero"],
            all(item["parseval_ok"] for item in record_reports),
            all(item["max_reconstruction_error"] < 1e-9 for item in record_reports),
            all(item["coeff_matches_shipped"] for item in record_reports),
        ]
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
