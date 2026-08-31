#!/usr/bin/env python3
"""Independent numerical verification of 4x4 orthonormal moment basis (1215-M2-S1)."""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --- Centered coordinates ---
COORDS_1D = [k - 1.5 for k in range(4)]  # -3/2 .. 3/2


def phi_1d(p: int, t: float) -> float:
    if p == 0:
        return 0.5
    if p == 1:
        return t / math.sqrt(5)
    if p == 2:
        return (t * t - 1.25) / 2
    if p == 3:
        return math.sqrt(5 / 9) * (t**3 - (41 / 20) * t)
    raise ValueError(f"invalid degree {p}")


BASIS_1D = [[phi_1d(p, t) for t in COORDS_1D] for p in range(4)]


def mode(p: int, q: int) -> list[float]:
    return [BASIS_1D[p][i] * BASIS_1D[q][j] for i in range(4) for j in range(4)]


MODES = {(p, q): mode(p, q) for p in range(4) for q in range(4)}


def inner(f: list[float], g: list[float]) -> float:
    return sum(a * b for a, b in zip(f, g))


def order_key(pq: tuple[int, int]) -> tuple[int, int, int, int]:
    p, q = pq
    return (p + q, max(p, q), p, q)


COMPLETE_ORDER = sorted(MODES.keys(), key=order_key)
HIGHER_MOMENTS = [pq for pq in COMPLETE_ORDER if pq[0] + pq[1] >= 2]

TOL_ORTHO = 1e-12
TOL_PARSEVAL = 1e-12
TOL_RECON = 1e-10
TOL_ZERO = 1e-9


def check_orthogonality_1d() -> float:
    worst = 0.0
    for p in range(4):
        for q in range(4):
            v = abs(inner(BASIS_1D[p], BASIS_1D[q]) - (1.0 if p == q else 0.0))
            worst = max(worst, v)
    return worst


def check_orthogonality_2d() -> float:
    worst = 0.0
    keys = list(MODES.keys())
    for a in keys:
        for b in keys:
            v = abs(inner(MODES[a], MODES[b]) - (1.0 if a == b else 0.0))
            worst = max(worst, v)
    return worst


def check_parseval_and_reconstruction(trials: int = 10) -> tuple[float, float]:
    rng = random.Random(20260709)
    worst_parseval = 0.0
    worst_recon = 0.0
    for _ in range(trials):
        f = [rng.uniform(-100, 100) for _ in range(16)]
        coeffs = {k: inner(f, MODES[k]) for k in MODES}
        e_direct = inner(f, f)
        e_coeff = sum(c * c for c in coeffs.values())
        rel = abs(e_direct - e_coeff) / max(1.0, abs(e_direct))
        worst_parseval = max(worst_parseval, rel)
        recon = [
            sum(coeffs[k] * MODES[k][i] for k in MODES) for i in range(16)
        ]
        err = max(abs(recon[i] - f[i]) for i in range(16))
        worst_recon = max(worst_recon, err)
    return worst_parseval, worst_recon


def energy_metrics(field: list[float], retained: set[tuple[int, int]]) -> dict:
    coeffs = {k: inner(field, MODES[k]) for k in MODES}
    e_total = sum(c * c for c in coeffs.values())
    e_dc = coeffs[(0, 0)] ** 2
    e_nonconst = e_total - e_dc
    e_retained = sum(coeffs[k] ** 2 for k in retained)

    def safe_div(num: float, den: float) -> float:
        return num / den if abs(den) > 1e-15 else 0.0

    dc_in_s = (0, 0) in retained
    retained_nonconst = e_retained - (e_dc if dc_in_s else 0.0)

    return {
        "E_total": e_total,
        "E_dc": e_dc,
        "E_nonconst": e_nonconst,
        "E_retained": e_retained,
        "E_residual": e_total - e_retained,
        "retained_frac_total": safe_div(e_retained, e_total),
        "retained_frac_nonconst": safe_div(retained_nonconst, e_nonconst),
    }


def main() -> int:
    off1 = check_orthogonality_1d()
    off2 = check_orthogonality_2d()
    parseval, recon = check_parseval_and_reconstruction()

    magic = [16, 3, 2, 13, 5, 10, 11, 8, 9, 6, 7, 12, 4, 15, 14, 1]
    const = [7.0] * 16

    em_magic = energy_metrics(magic, set(HIGHER_MOMENTS))
    em_const = energy_metrics(const, set(HIGHER_MOMENTS))

    checks = {
        "orthogonality_1d_max": off1,
        "orthogonality_2d_max": off2,
        "parseval_max_rel_err": parseval,
        "reconstruction_max_abs_err": recon,
        "magic_higher_equals_nonconst": abs(
            em_magic["E_retained"] - em_magic["E_nonconst"]
        ),
        "constant_E_nonconst": em_const["E_nonconst"],
        "constant_retained_frac_nonconst": em_const["retained_frac_nonconst"],
    }

    passed = (
        off1 < TOL_ORTHO
        and off2 < TOL_ORTHO
        and parseval < TOL_PARSEVAL
        and recon < TOL_RECON
        and checks["magic_higher_equals_nonconst"] < TOL_ZERO
        and em_const["E_nonconst"] < 1e-15
        and em_const["retained_frac_nonconst"] == 0.0
    )

    report = {"passed": passed, "tolerances": {
        "ortho": TOL_ORTHO, "parseval": TOL_PARSEVAL, "recon": TOL_RECON
    }, "checks": checks, "magic_energy": em_magic, "constant_energy": em_const}

    out = ROOT / "S1_verify_output.json"
    out.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps(report, indent=2))
    print(f"\n{'PASS' if passed else 'FAIL'} — wrote {out}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
