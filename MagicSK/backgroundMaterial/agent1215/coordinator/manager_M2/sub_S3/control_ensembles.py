#!/usr/bin/env python3
"""
Deterministic control ensembles for 4×4 grids:
  - Fisher–Yates uniform random permutations
  - Sequential k-transposition perturbations (k = 1, 2, 3)

Standard library only. PRNG matches control_ensembles.js (Mulberry32, uint32).
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator, Literal, Sequence

# ---------------------------------------------------------------------------
# Deterministic PRNG (Mulberry32) — must match control_ensembles.js
# ---------------------------------------------------------------------------

MASK32 = 0xFFFFFFFF
UINT32_RANGE = 1 << 32

# Domain-separation tags for independent permutation vs swap RNG streams
PERM_DOMAIN = 0x5065524D  # "PeRM"
SWAP_DOMAIN = 0x53574150  # "SWAP"


def _u32(x: int) -> int:
    return x & MASK32


def mulberry32_next_u32(state: int) -> tuple[int, int]:
    """Return (raw uint32 output, next_state)."""
    state = _u32(state + 0x6D2B79F5)
    t = state
    t = _u32((t ^ (t >> 15)) * _u32(t | 1))
    t = _u32(t ^ _u32(t + _u32((t ^ (t >> 7)) * _u32(t | 61))))
    return _u32(t ^ (t >> 14)), state


def mulberry32_next(state: int) -> tuple[float, int]:
    """Return (u in [0, 1), next_state)."""
    raw, state = mulberry32_next_u32(state)
    return raw / UINT32_RANGE, state


def rand_below(state: int, n: int) -> tuple[int, int]:
    """
    Uniform integer in [0, n) via rejection sampling on raw uint32.

    floor(u * n) from float u in [0, 1) is biased unless n divides 2^32.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    limit = (UINT32_RANGE // n) * n
    while True:
        raw, state = mulberry32_next_u32(state)
        if raw < limit:
            return raw % n, state


def seed_to_state(seed: int) -> int:
    """Map user seed to uint32 PRNG state (non-zero)."""
    s = _u32(seed)
    return s if s != 0 else 1


# ---------------------------------------------------------------------------
# Grid helpers — row-major flat index 0..15
# ---------------------------------------------------------------------------

N_CELLS = 16
GRID_SIDE = 4
COORDS_1D = [-1.5, -0.5, 0.5, 1.5]

# All 120 unordered distinct cell pairs with a < b
UNORDERED_PAIRS: tuple[tuple[int, int], ...] = tuple(
    (i, j) for i in range(N_CELLS) for j in range(i + 1, N_CELLS)
)
PAIR_TO_ID = {p: i for i, p in enumerate(UNORDERED_PAIRS)}


def flat_to_grid(flat: Sequence[int]) -> list[list[int]]:
    if len(flat) != N_CELLS:
        raise ValueError("expected 16 cells")
    return [list(flat[r * GRID_SIDE : (r + 1) * GRID_SIDE]) for r in range(GRID_SIDE)]


def grid_to_flat(grid: Sequence[Sequence[int]]) -> list[int]:
    return [grid[r][c] for r in range(GRID_SIDE) for c in range(GRID_SIDE)]


def apply_swap(flat: list[int], pair: tuple[int, int]) -> None:
    a, b = pair
    if a == b:
        raise ValueError("no-op swap forbidden")
    flat[a], flat[b] = flat[b], flat[a]


# ---------------------------------------------------------------------------
# Fisher–Yates unbiased permutation
# ---------------------------------------------------------------------------


def fisher_yates(values: Sequence[int], state: int) -> tuple[list[int], int]:
    arr = list(values)
    n = len(arr)
    for i in range(n - 1, 0, -1):
        j, state = rand_below(state, i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr, state


# ---------------------------------------------------------------------------
# Swap protocol configuration
# ---------------------------------------------------------------------------

PairSampling = Literal[
    "uniform_with_replacement",  # each step: uniform among 120 pairs (default)
    "distinct_pairs_no_replacement",  # k pairs all different within replicate
    "no_immediate_undo",  # reject pair equal to previous step's pair
    "distinct_pairs_no_immediate_undo",  # both constraints
]

AcrossKDesign = Literal["paired_prefix", "independent_resample"]


@dataclass(frozen=True)
class SwapProtocol:
    """
    Sequential transposition protocol on cell positions.

    A *transposition* swaps the values at two distinct cells (a, b), a != b.
    Pairs are unordered: (a, b) == (b, a). No-ops (a == b) are forbidden.
    """

    pair_sampling: PairSampling = "distinct_pairs_no_replacement"
    across_k: AcrossKDesign = "paired_prefix"
    forbid_immediate_undo: bool = False  # alias convenience; merged into sampling mode

    def effective_sampling(self) -> PairSampling:
        if self.pair_sampling != "uniform_with_replacement":
            return self.pair_sampling
        if self.forbid_immediate_undo:
            return "no_immediate_undo"
        return "uniform_with_replacement"


@dataclass
class SwapTrace:
    k: int
    pairs: list[tuple[int, int]]
    flat: list[int]


def _sample_pair(
    state: int,
    mode: PairSampling,
    used_pairs: set[tuple[int, int]],
    prev_pair: tuple[int, int] | None,
) -> tuple[tuple[int, int], int]:
    max_attempts = 512
    for _ in range(max_attempts):
        idx, state = rand_below(state, len(UNORDERED_PAIRS))
        pair = UNORDERED_PAIRS[idx]
        if mode in ("distinct_pairs_no_replacement", "distinct_pairs_no_immediate_undo"):
            if pair in used_pairs:
                continue
        if mode in ("no_immediate_undo", "distinct_pairs_no_immediate_undo"):
            if prev_pair is not None and pair == prev_pair:
                continue
        return pair, state
    raise RuntimeError(f"failed to sample pair under mode={mode}")


def sequential_swaps(
    base: Sequence[int],
    k: int,
    state: int,
    protocol: SwapProtocol,
) -> tuple[list[int], list[tuple[int, int]], int]:
    if k < 0:
        raise ValueError("k must be non-negative")
    flat = list(base)
    pairs: list[tuple[int, int]] = []
    mode = protocol.effective_sampling()
    used: set[tuple[int, int]] = set()
    prev: tuple[int, int] | None = None
    for _ in range(k):
        pair, state = _sample_pair(state, mode, used, prev)
        apply_swap(flat, pair)
        pairs.append(pair)
        used.add(pair)
        prev = pair
    return flat, pairs, state


def swap_ensemble_for_k_values(
    base: Sequence[int],
    k_values: Sequence[int],
    state: int,
    protocol: SwapProtocol,
) -> tuple[dict[int, SwapTrace], int]:
    """Generate perturbations for each k under paired or independent design."""
    kmax = max(k_values)
    traces: dict[int, SwapTrace] = {}
    if protocol.across_k == "paired_prefix":
        flat = list(base)
        pairs_so_far: list[tuple[int, int]] = []
        used: set[tuple[int, int]] = set()
        prev: tuple[int, int] | None = None
        mode = protocol.effective_sampling()
        for step in range(1, kmax + 1):
            pair, state = _sample_pair(state, mode, used, prev)
            apply_swap(flat, pair)
            pairs_so_far.append(pair)
            used.add(pair)
            prev = pair
            if step in k_values:
                traces[step] = SwapTrace(k=step, pairs=list(pairs_so_far), flat=list(flat))
    else:
        for k in sorted(k_values):
            flat, pairs, state = sequential_swaps(base, k, state, protocol)
            traces[k] = SwapTrace(k=k, pairs=pairs, flat=flat)
    return traces, state


# ---------------------------------------------------------------------------
# Orthonormal spatial moment basis (4×4, uniform weights)
# ---------------------------------------------------------------------------

def _gram_schmidt_1d(degree_max: int = 3) -> list[list[float]]:
    """Orthonormal polynomials on COORDS_1D with inner product <f,g> = mean(f*g)."""
    n = len(COORDS_1D)
    monomials = [[x**p for x in COORDS_1D] for p in range(degree_max + 1)]
    basis: list[list[float]] = []
    for raw in monomials:
        v = list(raw)
        for b in basis:
            proj = sum(v[i] * b[i] for i in range(n)) / n
            v = [v[i] - proj * b[i] for i in range(n)]
        norm = math.sqrt(sum(x * x for x in v) / n)
        if norm < 1e-12:
            raise ValueError("dependent monomial during Gram–Schmidt")
        basis.append([x / norm for x in v])
    return basis


PHI_1D = _gram_schmidt_1d(3)


@dataclass(frozen=True)
class MomentMode:
    p: int
    q: int
    degree: int
    index: int


def moment_modes() -> list[MomentMode]:
    modes: list[MomentMode] = []
    idx = 0
    for degree in range(7):
        for p in range(4):
            q = degree - p
            if 0 <= q <= 3:
                modes.append(MomentMode(p=p, q=q, degree=degree, index=idx))
                idx += 1
    return modes


MOMENT_MODES = moment_modes()


def eval_basis_2d(p: int, q: int, row: int, col: int) -> float:
    return PHI_1D[p][col] * PHI_1D[q][row]


def moment_coefficients(flat: Sequence[int]) -> list[float]:
    grid = flat_to_grid(flat)
    coeffs: list[float] = []
    for mode in MOMENT_MODES:
        acc = 0.0
        for r in range(GRID_SIDE):
            for c in range(GRID_SIDE):
                psi = eval_basis_2d(mode.p, mode.q, r, c)
                acc += grid[r][c] * psi
        coeffs.append(acc / N_CELLS)
    return coeffs


@dataclass(frozen=True)
class EnergyMetrics:
    total: float
    retained: float
    residual: float
    by_degree: dict[int, float]

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "retained": self.retained,
            "residual": self.residual,
            "by_degree": dict(self.by_degree),
        }


def energy_metrics(
    flat: Sequence[int],
    retain_max_degree: int = 1,
) -> EnergyMetrics:
    coeffs = moment_coefficients(flat)
    by_degree: dict[int, float] = {d: 0.0 for d in range(7)}
    for c, mode in zip(coeffs, MOMENT_MODES):
        by_degree[mode.degree] += c * c
    total = sum(by_degree.values())
    retained = sum(e for d, e in by_degree.items() if d <= retain_max_degree)
    residual = total - retained
    return EnergyMetrics(total=total, retained=retained, residual=residual, by_degree=by_degree)


def parseval_check(flat: Sequence[int]) -> float:
    """Should be ~0: ||grid||^2/N - sum c_k^2."""
    mean_square = sum(v * v for v in flat) / N_CELLS
    coeffs = moment_coefficients(flat)
    coeff_energy = sum(c * c for c in coeffs)
    return mean_square - coeff_energy


# ---------------------------------------------------------------------------
# Ensemble generation and statistical summaries
# ---------------------------------------------------------------------------

Condition = Literal["rand", "swap1", "swap2", "swap3"]


@dataclass
class EnsembleConfig:
    seed: int = 1215
    n_replicates: int = 200
    retain_max_degree: int = 1
    swap_protocol: SwapProtocol = field(default_factory=SwapProtocol)
    k_values: tuple[int, ...] = (1, 2, 3)


def derive_replicate_seed(
    base_seed: int,
    square_id: int,
    replicate: int,
    domain: int = 0,
) -> int:
    """Deterministic per-(square, replicate, domain) seed mixing."""
    x = _u32(base_seed)
    x = _u32(x ^ _u32(square_id * 0x9E3779B1))
    x = _u32(x ^ _u32(replicate * 0x85EBCA77))
    if domain:
        x = _u32(x ^ domain)
    return x if x != 0 else 1


@dataclass
class ReplicateMetrics:
    condition: Condition
    replicate: int
    energy: EnergyMetrics
    flat: list[int] | None = None


def generate_replicate_for_square(
    square_id: int,
    base_flat: Sequence[int],
    condition: Condition,
    replicate: int,
    cfg: EnsembleConfig,
) -> ReplicateMetrics:
    if condition == "rand":
        state = seed_to_state(
            derive_replicate_seed(cfg.seed, square_id, replicate, PERM_DOMAIN)
        )
        flat, _ = fisher_yates(list(base_flat), state)
    else:
        state = seed_to_state(
            derive_replicate_seed(cfg.seed, square_id, replicate, SWAP_DOMAIN)
        )
        k = int(condition[-1])
        if cfg.swap_protocol.across_k == "paired_prefix" and condition.startswith("swap"):
            traces, _ = swap_ensemble_for_k_values(
                base_flat, (1, 2, 3), state, cfg.swap_protocol
            )
            flat = traces[k].flat
        else:
            traces, _ = swap_ensemble_for_k_values(base_flat, (k,), state, cfg.swap_protocol)
            flat = traces[k].flat
    return ReplicateMetrics(
        condition=condition,
        replicate=replicate,
        energy=energy_metrics(flat, cfg.retain_max_degree),
        flat=flat,
    )


def quantile(sorted_vals: Sequence[float], q: float) -> float:
    if not sorted_vals:
        raise ValueError("empty")
    if q <= 0:
        return sorted_vals[0]
    if q >= 1:
        return sorted_vals[-1]
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    w = pos - lo
    return sorted_vals[lo] * (1 - w) + sorted_vals[hi] * w


@dataclass
class ConditionSummary:
    condition: Condition
    n: int
    mean_total: float
    std_total: float
    mean_retained: float
    mean_residual: float
    q05_residual: float
    q50_residual: float
    q95_residual: float

    def as_dict(self) -> dict:
        return {
            "condition": self.condition,
            "n": self.n,
            "mean_total": self.mean_total,
            "std_total": self.std_total,
            "mean_retained": self.mean_retained,
            "mean_residual": self.mean_residual,
            "q05_residual": self.q05_residual,
            "q50_residual": self.q50_residual,
            "q95_residual": self.q95_residual,
        }


def summarize_condition(values: list[EnergyMetrics], condition: Condition) -> ConditionSummary:
    totals = [v.total for v in values]
    retained = [v.retained for v in values]
    residuals = [v.residual for v in values]
    residuals_sorted = sorted(residuals)
    return ConditionSummary(
        condition=condition,
        n=len(values),
        mean_total=statistics.fmean(totals),
        std_total=statistics.pstdev(totals) if len(totals) > 1 else 0.0,
        mean_retained=statistics.fmean(retained),
        mean_residual=statistics.fmean(residuals),
        q05_residual=quantile(residuals_sorted, 0.05),
        q50_residual=quantile(residuals_sorted, 0.50),
        q95_residual=quantile(residuals_sorted, 0.95),
    )


def paired_swap_deltas(
    square_id: int,
    base_flat: Sequence[int],
    cfg: EnsembleConfig,
) -> dict[str, list[float]]:
    """Per-replicate residual deltas vs swap1 baseline under paired_prefix."""
    deltas: dict[str, list[float]] = {"swap2_minus_swap1": [], "swap3_minus_swap2": []}
    for rep in range(cfg.n_replicates):
        state = seed_to_state(
            derive_replicate_seed(cfg.seed, square_id, rep, SWAP_DOMAIN)
        )
        traces, _ = swap_ensemble_for_k_values(base_flat, (1, 2, 3), state, cfg.swap_protocol)
        e1 = energy_metrics(traces[1].flat, cfg.retain_max_degree).residual
        e2 = energy_metrics(traces[2].flat, cfg.retain_max_degree).residual
        e3 = energy_metrics(traces[3].flat, cfg.retain_max_degree).residual
        deltas["swap2_minus_swap1"].append(e2 - e1)
        deltas["swap3_minus_swap2"].append(e3 - e2)
    return deltas


def load_first_square(csv_path: Path) -> tuple[int, list[int]]:
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        square_id = int(row["id"])
        flat = [int(row[f"cell_{i}"]) for i in range(1, 17)]
        return square_id, flat


def run_demo(csv_path: Path | None, cfg: EnsembleConfig) -> dict:
    if csv_path and csv_path.exists():
        square_id, base = load_first_square(csv_path)
    else:
        square_id, base = 0, [1, 2, 15, 16, 12, 14, 3, 5, 13, 7, 10, 4, 8, 11, 6, 9]

    base_energy = energy_metrics(base, cfg.retain_max_degree)
    parseval_err = parseval_check(base)

    summaries: dict[str, ConditionSummary] = {}
    conditions: list[Condition] = ["rand", "swap1", "swap2", "swap3"]
    for cond in conditions:
        reps: list[EnergyMetrics] = []
        for rep in range(cfg.n_replicates):
            m = generate_replicate_for_square(square_id, base, cond, rep, cfg)
            reps.append(m.energy)
        summaries[cond] = summarize_condition(reps, cond)

    deltas = paired_swap_deltas(square_id, base, cfg)

    # Determinism spot-check (permutation stream, base multiset shuffle)
    perm_a = seed_to_state(derive_replicate_seed(cfg.seed, square_id, 0, PERM_DOMAIN))
    flat_a, _ = fisher_yates(list(base), perm_a)
    perm_c = seed_to_state(derive_replicate_seed(cfg.seed, square_id, 0, PERM_DOMAIN))
    flat_c, _ = fisher_yates(list(base), perm_c)

    # Single-replicate parity anchors for Node cross-check
    swap_state = seed_to_state(
        derive_replicate_seed(cfg.seed, square_id, 0, SWAP_DOMAIN)
    )
    swap_traces, _ = swap_ensemble_for_k_values(
        base, (1, 2, 3), swap_state, cfg.swap_protocol
    )
    swap1_residual = energy_metrics(
        swap_traces[1].flat, cfg.retain_max_degree
    ).residual

    return {
        "square_id": square_id,
        "base_flat": base,
        "base_energy": base_energy.as_dict(),
        "parseval_error": parseval_err,
        "config": {
            "seed": cfg.seed,
            "n_replicates": cfg.n_replicates,
            "retain_max_degree": cfg.retain_max_degree,
            "swap_protocol": {
                "pair_sampling": cfg.swap_protocol.effective_sampling(),
                "across_k": cfg.swap_protocol.across_k,
            },
            "rng_domains": {
                "perm": hex(PERM_DOMAIN),
                "swap": hex(SWAP_DOMAIN),
            },
            "smoke_replicates": cfg.n_replicates,
            "production_replicates_recommended": 2000,
        },
        "summaries": {k: v.as_dict() for k, v in summaries.items()},
        "paired_deltas": {
            name: {
                "mean": statistics.fmean(vals),
                "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
                "q05": quantile(sorted(vals), 0.05),
                "q95": quantile(sorted(vals), 0.95),
            }
            for name, vals in deltas.items()
        },
        "determinism_check": {
            "fisher_yates_rep0_match": flat_a == flat_c,
            "first_rand_perm_head": flat_a[:8],
            "swap1_residual_rep0": swap1_residual,
            "rand_below_method": "rejection_uint32",
        },
    }


def main() -> None:
    here = Path(__file__).resolve().parent
    csv_default = Path(
        "/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv"
    )
    cfg = EnsembleConfig(
        seed=1215,
        n_replicates=200,
        retain_max_degree=1,
        swap_protocol=SwapProtocol(
            pair_sampling="distinct_pairs_no_replacement",
            across_k="paired_prefix",
        ),
    )
    result = run_demo(csv_default if csv_default.exists() else None, cfg)

    print("=== S3 Control Ensemble Demo (4×4) ===")
    print(json.dumps(result, indent=2))

    out_path = here / "simulation_output.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
