#!/usr/bin/env python3
"""Numerical verification of centered 4×4 orthonormal tensor-product basis."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

N = 4
MEAN_HEIGHT = 8.5
MAGIC_SUM = 34
COORDINATES = (-1.5, -0.5, 0.5, 1.5)

# Browser-style tolerances (IEEE-754 double, 16-term sums, 8-decimal display)
TOL_GRAM = 1e-12
TOL_RECON = 1e-12
TOL_PARSEVAL = 1e-12
TOL_ZERO_DETECT = 1e-8  # analyze.py rounds coefficients to 8 decimals
TOL_BROWSER_GRAM = 1e-10
TOL_BROWSER_ZERO = 1e-6
TOL_DIAG_REL = 1e-9


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def orthonormal_polynomials() -> list[list[float]]:
    """Gram–Schmidt monomials on the four centered cell coordinates."""
    basis: list[list[float]] = []
    for degree in range(N):
        vector = [coordinate**degree for coordinate in COORDINATES]
        for previous in basis:
            projection = dot(vector, previous)
            vector = [value - projection * prior for value, prior in zip(vector, previous)]
        norm = math.sqrt(dot(vector, vector))
        basis.append([value / norm for value in vector])
    return basis


def phi3_closed_form(t: float) -> float:
    """Degree-3 orthonormal polynomial: sqrt(5/9) * (t^3 - (41/20)t)."""
    return math.sqrt(5 / 9) * (t**3 - (41 / 20) * t)


def phi3_alt_form(t: float) -> float:
    """Equivalent sample values [-1, 3, -3, 1] / (2*sqrt(5)) on S."""
    index = COORDINATES.index(t)
    numerators = (-1, 3, -3, 1)
    return numerators[index] / (2 * math.sqrt(5))


BASIS_1D = orthonormal_polynomials()


def assert_phi3_equivalence() -> None:
    """Verify closed-form φ₃ matches Gram–Schmidt and alternate rational form."""
    for t in COORDINATES:
        closed = phi3_closed_form(t)
        alt = phi3_alt_form(t)
        assert abs(closed - alt) < 1e-14, f"φ₃ closed vs alt at t={t}: {closed} vs {alt}"
    gs = BASIS_1D[3]
    for i, t in enumerate(COORDINATES):
        closed = phi3_closed_form(t)
        assert abs(closed - gs[i]) < 1e-14, f"φ₃ closed vs GS at t={t}: {closed} vs {gs[i]}"
        assert abs(gs[i] - phi3_alt_form(t)) < 1e-14, f"φ₃ GS vs alt at t={t}"


def mode_index(row: int, col: int) -> int:
    return row * N + col


def mode_value(p: int, q: int, row: int, col: int) -> float:
    """Tensor mode M_pq: x-degree p on column, y-degree q on row."""
    return BASIS_1D[p][col] * BASIS_1D[q][row]


def build_modes() -> list[list[float]]:
    """16 modes in row-major (p,q) order matching S1 mode_order."""
    order = [
        (0, 0), (0, 1), (1, 0), (1, 1),
        (0, 2), (2, 0), (1, 2), (2, 1),
        (0, 3), (3, 0), (2, 2), (1, 3),
        (3, 1), (2, 3), (3, 2), (3, 3),
    ]
    modes: list[list[float]] = []
    for p, q in order:
        flat = [
            mode_value(p, q, row, col)
            for row in range(N)
            for col in range(N)
        ]
        modes.append(flat)
    return modes


MODES = build_modes()
MODE_LABELS = [
    "M00", "M01", "M10", "M11",
    "M02", "M20", "M12", "M21",
    "M03", "M30", "M22", "M13",
    "M31", "M23", "M32", "M33",
]


def matrix_from_flat(cells: list[int]) -> list[list[float]]:
    return [cells[offset : offset + N] for offset in range(0, N * N, N)]


def centered_heights(cells: list[int]) -> list[list[float]]:
    square = matrix_from_flat(cells)
    return [[value - MEAN_HEIGHT for value in row] for row in square]


def heights_flat(cells: list[int]) -> list[float]:
    return [value for row in centered_heights(cells) for value in row]


def coefficient(cells: list[int], p: int, q: int) -> float:
    heights = centered_heights(cells)
    return sum(
        BASIS_1D[p][col] * BASIS_1D[q][row] * heights[row][col]
        for row in range(N)
        for col in range(N)
    )


def diagonal_coefficients(cells: list[int]) -> tuple[float, float, float]:
    """Return (c11, c22, c33) for centered heights."""
    return (
        coefficient(cells, 1, 1),
        coefficient(cells, 2, 2),
        coefficient(cells, 3, 3),
    )


def diagonal_relations(cells: list[int]) -> dict[str, float]:
    c11, c22, c33 = diagonal_coefficients(cells)
    return {
        "c11": c11,
        "c22": c22,
        "c33": c33,
        "main_balance": c11 + c22 + c33,
        "anti_balance": -c11 + c22 - c33,
        "c33_equals_neg_c11": c33 + c11,
    }


def assert_diagonal_relations_on_full_magic(cells: list[int], label: str) -> None:
    """Full magic (both diagonals = 34) forces c22=0 and c33=-c11."""
    rel = diagonal_relations(cells)
    assert abs(rel["main_balance"]) < TOL_DIAG_REL, (
        f"{label}: main diagonal balance c11+c22+c33 != 0: {rel['main_balance']}"
    )
    assert abs(rel["anti_balance"]) < TOL_DIAG_REL, (
        f"{label}: anti diagonal balance -c11+c22-c33 != 0: {rel['anti_balance']}"
    )
    assert abs(rel["c22"]) < TOL_DIAG_REL, (
        f"{label}: c22 (M22) != 0 on full magic: {rel['c22']}"
    )
    assert abs(rel["c33_equals_neg_c11"]) < TOL_DIAG_REL, (
        f"{label}: c33 != -c11 on full magic: c33={rel['c33']}, c11={rel['c11']}"
    )


def all_coefficients(cells: list[int]) -> dict[str, float]:
    order = [
        (0, 0), (0, 1), (1, 0), (1, 1),
        (0, 2), (2, 0), (1, 2), (2, 1),
        (0, 3), (3, 0), (2, 2), (1, 3),
        (3, 1), (2, 3), (3, 2), (3, 3),
    ]
    return {f"M{p}{q}": coefficient(cells, p, q) for p, q in order}


def line_sums(cells: list[int]) -> dict[str, list[int]]:
    square = matrix_from_flat(cells)
    rows = [sum(row) for row in square]
    cols = [sum(square[row][col] for row in range(N)) for col in range(N)]
    diags = [
        sum(square[i][i] for i in range(N)),
        sum(square[i][N - 1 - i] for i in range(N)),
    ]
    return {"rows": rows, "columns": cols, "diagonals": diags}


def gram_matrix(modes: list[list[float]]) -> list[list[float]]:
    size = len(modes)
    return [[dot(modes[i], modes[j]) for j in range(size)] for i in range(size)]


def max_off_diagonal(gram: list[list[float]]) -> float:
    size = len(gram)
    worst = 0.0
    for i in range(size):
        for j in range(size):
            target = 1.0 if i == j else 0.0
            worst = max(worst, abs(gram[i][j] - target))
    return worst


def reconstruct(heights: list[float]) -> list[float]:
    coeffs = [dot(mode, heights) for mode in MODES]
    rebuilt = [0.0] * (N * N)
    for coeff, mode in zip(coeffs, MODES):
        rebuilt = [a + coeff * m for a, m in zip(rebuilt, mode)]
    return rebuilt


def parseval_error(heights: list[float]) -> float:
    coeffs = [dot(mode, heights) for mode in MODES]
    lhs = sum(c * c for c in coeffs)
    rhs = dot(heights, heights)
    return abs(lhs - rhs)


def simulate_js_float(x: float) -> float:
    """Round-trip through JavaScript Number (IEEE-754 double)."""
    import struct
    return struct.unpack("d", struct.pack("d", x))[0]


def gram_matrix_browser(modes: list[list[float]]) -> float:
    """Max Gram error when basis values are JS-rounded."""
    js_modes = [
        [simulate_js_float(v) for v in mode]
        for mode in modes
    ]
    gram = gram_matrix(js_modes)
    return max_off_diagonal(gram)


def is_row_magic(cells: list[int]) -> bool:
    sums = line_sums(cells)
    return all(value == MAGIC_SUM for value in sums["rows"])


def is_col_magic(cells: list[int]) -> bool:
    sums = line_sums(cells)
    return all(value == MAGIC_SUM for value in sums["columns"])


def is_semi_magic(cells: list[int]) -> bool:
    return is_row_magic(cells) and is_col_magic(cells)


def is_full_magic(cells: list[int]) -> bool:
    sums = line_sums(cells)
    return is_semi_magic(cells) and all(value == MAGIC_SUM for value in sums["diagonals"])


# --- Counterexample squares ---
ROW_ONLY = [1, 2, 15, 16, 3, 4, 13, 14, 5, 6, 11, 12, 7, 8, 9, 10]
KNOWN_MAGIC = [1, 2, 15, 16, 12, 14, 3, 5, 13, 7, 10, 4, 8, 11, 6, 9]


def find_semi_magic_non_diagonal() -> list[int] | None:
    """Find a permutation with row/col=34 but failing at least one diagonal."""
    base = matrix_from_flat(KNOWN_MAGIC)
    for col_a in range(N):
        for col_b in range(col_a + 1, N):
            trial = [row[:] for row in base]
            for row in trial:
                row[col_a], row[col_b] = row[col_b], row[col_a]
            cells = [v for row in trial for v in row]
            if is_semi_magic(cells) and not is_full_magic(cells):
                return cells
            trial = [row[:] for row in base]
            trial[col_a], trial[col_b] = trial[col_b], trial[col_a]
            cells = [v for row in trial for v in row]
            if is_semi_magic(cells) and not is_full_magic(cells):
                return cells
    return None


def analyze_constraint_batch(
    squares: list[tuple[str, list[int]]],
    labels: list[str],
) -> dict:
    results = {}
    for name, cells in squares:
        coeffs = all_coefficients(cells)
        subset = {label: coeffs[label] for label in labels}
        diag = diagonal_relations(cells)
        results[name] = {
            "lineSums": line_sums(cells),
            "coefficients": {k: round(v, 10) for k, v in subset.items()},
            "diagonalRelations": {k: round(v, 10) for k, v in diag.items()},
            "flags": {
                "rowMagic": is_row_magic(cells),
                "colMagic": is_col_magic(cells),
                "semiMagic": is_semi_magic(cells),
                "fullMagic": is_full_magic(cells),
            },
        }
    return results


def scan_magic_coefficient_zeros(cells_list: list[list[int]]) -> dict[str, dict]:
    """For a batch of full magic squares, report max |coeff| per mode."""
    labels = [f"M{p}{q}" for p in range(4) for q in range(4) if not (p == 0 and q == 0)]
    max_abs = {label: 0.0 for label in labels}
    always_zero: dict[str, bool] = {label: True for label in labels}
    for cells in cells_list:
        coeffs = all_coefficients(cells)
        for label in labels:
            value = abs(coeffs[label])
            max_abs[label] = max(max_abs[label], value)
            if value > TOL_ZERO_DETECT:
                always_zero[label] = False
    return {
        "count": len(cells_list),
        "maxAbs": {k: round(v, 10) for k, v in sorted(max_abs.items())},
        "forcedZero": {k: v for k, v in sorted(always_zero.items())},
    }


def main() -> int:
    out_lines: list[str] = []
    results: dict = {}

    def log(msg: str = "") -> None:
        out_lines.append(msg)
        print(msg)

    log("=" * 72)
    log("S2 — Centered 4×4 orthonormal tensor-product basis verification")
    log("=" * 72)

    # 0. φ₃ closed-form equivalence
    log("\n--- 0. Degree-3 closed form φ₃(t) = √(5/9)·(t³ − (41/20)t) ---")
    assert_phi3_equivalence()
    log("  ASSERT PASS: φ₃ closed form ≡ [-1,3,-3,1]/(2√5) ≡ Gram–Schmidt samples")
    for i, t in enumerate(COORDINATES):
        log(
            f"  t={t:+.1f}: closed={phi3_closed_form(t):+.12f}  "
            f"alt={phi3_alt_form(t):+.12f}  GS={BASIS_1D[3][i]:+.12f}"
        )

    # 1. Basis specification
    log("\n--- 1. Centered coordinates and 1D Gram–Schmidt basis ---")
    log(f"Coordinates: {COORDINATES}")
    for degree, poly in enumerate(BASIS_1D):
        norm = math.sqrt(dot(poly, poly))
        log(f"  φ_{degree}: {[round(v, 12) for v in poly]}  (‖φ_{degree}‖²={norm:.15f})")

    gram_1d = gram_matrix(BASIS_1D)
    err_1d = max_off_diagonal(gram_1d)
    log(f"1D Gram max deviation from I₄: {err_1d:.3e}")

    # 2. All 16 modes
    log("\n--- 2. Sixteen 2D tensor-product modes (row-major flatten) ---")
    for label, mode in zip(MODE_LABELS, MODES):
        norm = math.sqrt(dot(mode, mode))
        log(f"  {label}: ‖ψ‖²={norm:.15f}")

    # 3. Gram matrix
    log("\n--- 3. Full 16×16 Gram matrix (orthogonality) ---")
    gram = gram_matrix(MODES)
    err_gram = max_off_diagonal(gram)
    log(f"Max |G − I| entry: {err_gram:.3e}  (pass threshold {TOL_GRAM:.0e}: {'PASS' if err_gram < TOL_GRAM else 'FAIL'})")

    # 4. Completeness / reconstruction
    log("\n--- 4. Completeness / reconstruction ---")
    test_squares = [
        ("known_magic", KNOWN_MAGIC),
        ("row_only", ROW_ONLY),
        ("checkerboard_pattern", [8.5 + (1 if (r + c) % 2 == 0 else -1) for r in range(N) for c in range(N)]),
    ]
    recon_errors = {}
    for name, cells in test_squares:
        heights = heights_flat(cells) if name != "checkerboard_pattern" else cells
        rebuilt = reconstruct(heights)
        err = max(abs(a - b) for a, b in zip(heights, rebuilt))
        recon_errors[name] = err
        log(f"  {name}: max reconstruction error = {err:.3e}")
    max_recon = max(recon_errors.values())
    log(f"Overall reconstruction: {'PASS' if max_recon < TOL_RECON else 'FAIL'} (max {max_recon:.3e})")

    # 5. Parseval
    log("\n--- 5. Parseval identity Σ c² = Σ h² ---")
    parseval_errors = {}
    for name, cells in test_squares:
        heights = heights_flat(cells) if name != "checkerboard_pattern" else cells
        err = parseval_error(heights)
        parseval_errors[name] = err
        log(f"  {name}: |Σc² − Σh²| = {err:.3e}")
    max_parseval = max(parseval_errors.values())
    log(f"Overall Parseval: {'PASS' if max_parseval < TOL_PARSEVAL else 'FAIL'} (max {max_parseval:.3e})")

    # 6. Browser float implications
    log("\n--- 6. Browser Number (IEEE-754) implications ---")
    js_gram_err = gram_matrix_browser(MODES)
    log(f"Gram max |G−I| after JS float round-trip on basis: {js_gram_err:.3e}")
    log(f"Recommended browser orthogonality tolerance: {TOL_BROWSER_GRAM:.0e}")
    log(f"Recommended browser zero-detection tolerance: {TOL_BROWSER_ZERO:.0e}")
    log(f"Display rounding (8 decimals, per analyze.py): use {TOL_ZERO_DETECT:.0e} for 'exactly zero'")

    # 7. Low-mode constraint analysis
    log("\n--- 7. Low-mode magic-constraint implications ---")

    col_only = [v for row in zip(*matrix_from_flat(ROW_ONLY)) for v in row]
    semi = find_semi_magic_non_diagonal()
    if semi is None:
        semi = [16, 3, 2, 13, 5, 10, 11, 8, 9, 6, 7, 12, 4, 15, 14, 1]

    constraint_squares = [
        ("row_only", ROW_ONLY),
        ("col_only_transpose", col_only),
        ("semi_magic", semi),
        ("known_magic", KNOWN_MAGIC),
    ]

    low_labels = [
        "M01", "M02", "M03", "M10", "M20", "M30",
        "M11", "M12", "M21", "M22", "M13", "M31", "M33",
    ]
    constraint_results = analyze_constraint_batch(constraint_squares, low_labels)
    results["constraintExamples"] = constraint_results

    log("\nConstraint counterexamples / examples:")
    for name, data in constraint_results.items():
        flags = data["flags"]
        log(f"\n  [{name}] row={flags['rowMagic']} col={flags['colMagic']} full={flags['fullMagic']}")
        log(f"    diagonals: {data['lineSums']['diagonals']}")
        for label in low_labels:
            value = data["coefficients"][label]
            mark = "~0" if abs(value) < TOL_ZERO_DETECT else "≠0"
            log(f"    {label} = {value:+.10f}  ({mark})")
        diag = data["diagonalRelations"]
        log(
            f"    diagonal balances: c11+c22+c33={diag['main_balance']:+.6f}, "
            f"-c11+c22-c33={diag['anti_balance']:+.6f}"
        )

    # 7b. Diagonal relation assertions on full magic
    log("\n--- 7b. Diagonal balance assertions (full magic only) ---")
    assert_diagonal_relations_on_full_magic(KNOWN_MAGIC, "known_magic")
    log("  ASSERT PASS [known_magic]: c11+c22+c33=0, -c11+c22-c33=0, c22=0, c33=-c11")
    rel_known = diagonal_relations(KNOWN_MAGIC)
    log(
        f"    c11={rel_known['c11']:+.6f}, c22={rel_known['c22']:+.6f}, "
        f"c33={rel_known['c33']:+.6f}"
    )

    # Semi-magic with failing diagonals is NOT a counterexample to diagonal forcing
    rel_semi = diagonal_relations(semi)
    log("\n  [semi_magic] diagonal balances (diagonals ≠ 34 — relations need not hold):")
    log(
        f"    c11+c22+c33={rel_semi['main_balance']:+.6f}, "
        f"-c11+c22-c33={rel_semi['anti_balance']:+.6f}, M22={rel_semi['c22']:+.6f}"
    )
    assert abs(rel_semi["c22"]) > TOL_ZERO_DETECT, "semi_magic should have nonzero M22"
    log("  CONFIRMED: semi-magic with failing diagonals has M22≠0 (not a diagonal-counterexample)")

    log("\n--- Forced vanishing (proved + verified numerically) ---")
    log("  Equal COLUMN sums (=34): M10, M20, M30 forced to 0 (pure-x modes factor through col sums).")
    log("  Equal ROW sums (=34):    M01, M02, M03 forced to 0 (pure-y modes factor through row sums).")
    log("  M00 excluded by centering (mean height removed).")
    log("  Both DIAGONAL sums (=34): c11+c22+c33=0 and -c11+c22-c33=0 ⇒ c22=0, c33=-c11.")

    log("\n--- NOT forced by row+column sums alone ---")
    log("  Interaction modes M11, M12, M21, M22, M13, M31, M23, M32, M33 can be nonzero.")
    log("  Row/column constraints alone do NOT force M22 (see synthetic margin-free field).")

    # 8. Batch scan on magic squares from CSV if available
    log("\n--- 8. Batch scan: coefficient zeros across magic squares ---")
    magic_squares: list[list[int]] = []
    csv_path = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv")
    if csv_path.exists():
        import csv

        with csv_path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                cells = [int(row[f"cell_{i}"]) for i in range(1, 17)]
                if is_full_magic(cells):
                    magic_squares.append(cells)
        log(f"Loaded {len(magic_squares)} full magic squares from CSV.")
    else:
        magic_squares = [KNOWN_MAGIC]
        log("CSV not found; scanning known_magic only.")

    for cells in magic_squares:
        assert_diagonal_relations_on_full_magic(cells, "batch_magic")
    log(f"  ASSERT PASS: diagonal relations hold on all {len(magic_squares)} full magic squares")

    scan = scan_magic_coefficient_zeros(magic_squares)
    results["magicScan"] = scan
    forced = [k for k, v in scan["forcedZero"].items() if v]
    not_forced = [k for k, v in scan["forcedZero"].items() if not v]
    log(f"Modes forced to 0 across all {scan['count']} scanned full magic squares: {forced}")
    log(f"Modes NOT universally zero: {not_forced}")
    log("Max |coefficient| across batch (selected):")
    for label in ["M11", "M12", "M21", "M22", "M31", "M33"]:
        log(f"  {label}: {scan['maxAbs'][label]}")

    # 9. Row/column-only counterexample for M22
    log("\n--- 9. Zero row/column margins do not force M22 = 0 ---")
    margin_h = [
        [1.0, -1.0, 0.5, -0.5],
        [-1.0, 1.0, -0.5, 0.5],
        [0.5, -0.5, -1.0, 1.0],
        [-0.5, 0.5, 1.0, -1.0],
    ]
    margin_flat = [v for row in margin_h for v in row]
    row_margins = [sum(margin_h[r][c] for c in range(N)) for r in range(N)]
    col_margins = [sum(margin_h[r][c] for r in range(N)) for c in range(N)]
    m22 = dot(MODES[MODE_LABELS.index("M22")], margin_flat)
    assert all(abs(m) < 1e-12 for m in row_margins + col_margins), "margin field must have zero row/col sums"
    assert abs(m22 + 1.0) < 1e-12, f"expected M22=-1, got {m22}"
    log(f"  Synthetic h with row sums {row_margins}, col sums {col_margins}")
    log(f"  M22 = {m22:+.10f}  (nonzero despite zero margins)")
    log("  ASSERT PASS: row/column-only constraints do not force M22=0")

    # Compile JSON output
    results.update({
        "phi3_closed_form": "sqrt(5/9) * (t^3 - (41/20)*t)",
        "phi3_alt_samples": "[-1, 3, -3, 1] / (2*sqrt(5))",
        "coordinates": COORDINATES,
        "basis_1d": BASIS_1D,
        "gram_1d_max_error": err_1d,
        "gram_16_max_error": err_gram,
        "reconstruction_errors": recon_errors,
        "parseval_errors": parseval_errors,
        "browser_gram_max_error": js_gram_err,
        "diagonalRelationsKnownMagic": {k: round(v, 10) for k, v in rel_known.items()},
        "diagonalRelationsSemiMagic": {k: round(v, 10) for k, v in rel_semi.items()},
        "rowColOnlyM22Counterexample": round(m22, 10),
        "tolerances": {
            "python_gram": TOL_GRAM,
            "python_recon": TOL_RECON,
            "python_parseval": TOL_PARSEVAL,
            "zero_detect": TOL_ZERO_DETECT,
            "browser_gram": TOL_BROWSER_GRAM,
            "browser_zero": TOL_BROWSER_ZERO,
            "diagonal_relations": TOL_DIAG_REL,
        },
        "theory": {
            "forcedByColSums": ["M10", "M20", "M30"],
            "forcedByRowSums": ["M01", "M02", "M03"],
            "forcedByCentering": ["M00"],
            "forcedByBothDiagonals": {
                "M22": "c22 = 0",
                "M33": "c33 = -c11 (paired with M11)",
                "relations": ["c11 + c22 + c33 = 0", "-c11 + c22 - c33 = 0"],
            },
            "notForcedByRowCol": [
                "M11", "M12", "M13", "M21", "M22", "M23", "M31", "M32", "M33",
            ],
            "semiMagicNotDiagonalCounterexample": (
                "Semi-magic with failing diagonals may have M22≠0; "
                "this does not refute diagonal forcing on full magic squares."
            ),
        },
    })

    out_dir = Path(__file__).resolve().parent
    json_path = out_dir / "verification_output.json"
    txt_path = out_dir / "verification_output.txt"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    txt_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    log(f"\nWrote {json_path.name} and {txt_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
