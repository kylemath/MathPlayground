# S2 Report — Formulas, Controls, and Reproducibility Audit

| Field | Value |
|---|---|
| **Agent** | 1215-M4-S2 |
| **Task** | Independent audit of basis math, Parseval, coefficient conventions, reconstruction, control definitions, seeds, null generation, sample aggregation, and reproducibility |
| **Manager** | 1215-M4 |
| **Status** | **Complete** |

---

## Work Product

Independent numerical and control audit of `MagicMomentExplorer` (read-only). All formulas in `scripts/analyze.py` were re-derived, tested on 4,400 shipped records, and reproduced by re-running the pipeline with seed `20260709`. **All core numerical claims pass.** One cross-stream discrepancy is flagged: M2’s Mulberry32 control prototype does not match the shipped Python `random.Random` implementation.

### 1. Basis construction and orthonormality

**Source definition** (`analyze.py` lines 40–56):

- Centered coordinates: `(-1.5, -0.5, 0.5, 1.5)` (column index `j`, row index `i`).
- 1D basis: Gram–Schmidt on monomials `t^p` for `p = 0..3`, normalized under the **discrete inner product** `⟨f,g⟩ = Σ_k f(t_k) g(t_k)` (no quadrature weights).
- 2D modes: separable tensor product `φ_p(x_j) φ_q(y_i)` over the 4×4 grid (16 modes total).

**Independent checks** (`scripts/basis_parseval_audit.py`):

| Check | Result | Max error |
|---|---|---|
| 1D Gram matrix = identity | PASS | 6.661×10⁻¹⁶ |
| 2D tensor Gram matrix = I₁₆ | PASS | < 10⁻¹² |
| Recomputed basis matches `analysis.json` metadata | PASS | < 10⁻⁹ per entry |

Shipped 1D basis (matches closed-form derivation in M2-S1 `S1_verify_basis.py`):

```
φ₀ = [0.5, 0.5, 0.5, 0.5]
φ₁ = [-0.6708203932, -0.2236067977, 0.2236067977, 0.6708203932]
φ₂ = [0.5, -0.5, -0.5, 0.5]
φ₃ = [-0.2236067977, 0.6708203932, -0.6708203932, 0.2236067977]
```

**Completeness:** Four orthonormal 1D vectors on four sample points span ℝ⁴; the 16 tensor products span the full 16-dimensional height space. This is the discrete analogue of a “complete orthonormal polynomial basis” on the fixed 4×4 lattice (as claimed in `index.html`).

### 2. Coefficient conventions

For centered heights `h_{ij} = a_{ij} - 8.5`:

```
c_{pq} = Σ_{i,j} φ_p(x_j) φ_q(y_i) h_{ij}     (p,q ∈ {0,1,2,3})
```

Naming: `M{p}{q}` where **first index = column (x) degree**, **second = row (y) degree**.

| Convention | Implementation |
|---|---|
| Stored coefficients | All `(p,q) ≠ (0,0)` — DC mode `M00` excluded from `coefficients` dict |
| Mode energy | `modeEnergy[Mpq] = c_{pq}²` |
| Axial energy | Modes with exactly one index zero: `M01, M02, M03, M10, M20, M30` (6 modes) |
| Interaction energy | Modes with both indices ≥ 1 (9 modes) |
| Degree energy `E_d` | Sum of interaction-mode energies with `p + q = d` for `d = 2..6` |
| Low-order energy | `E₂ + E₃` |
| Spectral centroid | `Σ_{d=2}^{6} d · E_d / interactionEnergy` (interaction only) |

**Full-record verification** (`scripts/full_record_scan.py`, 4,400 records): 0 coefficient mismatches (tolerance 10⁻⁵ vs shipped 8-decimal rounding).

### 3. Parseval identity and reconstruction

**Parseval (all 16 modes, including M00):**

```
Σ_{p,q} c_{pq}² = Σ_{i,j} h_{ij}²
```

| Scope | Failures |
|---|---|
| All 4,400 records | **0** |
| Sample records (magic, swap, random) | **0**; max reconstruction error ≤ 9.1×10⁻¹⁵ |

**Reconstruction:**

```
h_{ij} = Σ_{p,q} c_{pq} φ_p(x_j) φ_q(y_i)
```

Exact recovery on all records within floating-point tolerance.

**Energy partition:**

```
axialEnergy + interactionEnergy + c₀₀² = 340
```

0 failures across 4,400 records. The UI’s fixed height energy 340 is correct for any permutation of 1..16:

```
Σ(a−8.5)² = Σa² − 1156 = 1496 − 1156 = 340
```

### 4. Magic-square axial-zero claim

Empirical: all **880** magic cohort records have `axialEnergy = 0.0`.

Mechanism (consistent with row/column magic): each row and column of centered heights sums to zero (`4 × 8.5 = 34`). That annihilates all six axial modes under the discrete tensor basis. The UI claim “magic removes axial imbalance” is **numerically verified**.

### 5. Control definitions and null generation

**Shipped implementation** (`analyze.py`):

| Control | Method | Count | Still magic? |
|---|---|---|---|
| `magic` | Source CSV, unmodified | 880 | 880/880 |
| `swap-1` | `rng.sample(range(16), 2)` → one pair swap | 880 | 0/880 |
| `swap-2` | `rng.sample(range(16), 4)` → two pair swaps | 880 | 0/880 |
| `swap-3` | `rng.sample(range(16), 6)` → three pair swaps | 880 | 0/880 |
| `random` | `rng.shuffle([1..16])` | 880 | 0/880 |

- **PRNG:** `random.Random(20260709)` (Python Mersenne Twister).
- **RNG order:** 2,640 swap operations (3 × 880) consume RNG first; then 880 shuffles for random cohort.
- All swap outputs remain permutations of 1..16 (verified).

**Cell-level determinism** (`scripts/control_cells_match.py`): replayed full RNG stream; **0 mismatches** across 2,640 swap + 880 random records vs shipped `analysis.json`.

Example shipped controls (source id 1):

| Record | Cells (row-major) |
|---|---|
| S1-001 | `[1,2,15,16,12,9,3,5,13,7,10,4,8,11,6,14]` |
| S2-001 | `[1,13,15,16,12,14,3,5,2,11,10,4,8,7,6,9]` |
| S3-001 | `[1,2,15,5,4,14,3,16,13,6,10,12,8,11,7,9]` |
| R001 | `[16,14,10,5,9,15,3,7,12,13,4,2,8,6,1,11]` |

### 6. Sample aggregation

`summarize()` in `analyze.py` computes per-cohort means of `lineDefectEnergy`, `axialEnergy`, `lowOrderEnergy`, `spectralCentroid`, plus counts. Independent recomputation from shipped records **matches** `metadata.cohortSummary` exactly.

| Cohort | Count | Magic | Mean line defect | Mean axial E | Mean low-order E | Mean spectral degree |
|---|---|---|---|---|---|---|
| magic | 880 | 880 | 0.0 | 0.0 | 124.845091 | 4.0 |
| random | 880 | 0 | 677.177273 | 136.454545 | 66.846318 | 4.008771 |
| swap-1 | 880 | 0 | 161.654545 | 32.821023 | 111.983 | 3.998224 |
| swap-2 | 880 | 0 | 315.690909 | 63.56875 | 98.179864 | 3.99859 |
| swap-3 | 880 | 0 | 429.363636 | 84.6375 | 90.937568 | 3.986844 |

### 7. Reproducibility

**Command:**

```bash
python3 /Users/kylemathewson/MagicSK/MagicMomentExplorer/scripts/analyze.py \
  --input /Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv \
  --output-dir /Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/sub_S2/outputs/repro_run \
  --random-count 880 \
  --seed 20260709
```

**Observed stdout:**

```
Wrote 4400 records to .../repro_run/analysis.json, .../analysis.csv, and analysis-data.js
```

**Comparison vs shipped `data/analysis.json`:**

| Field | Result |
|---|---|
| All metadata fields (basis, cohortSummary, dudeneyCounts, seed, counts) | **Match** |
| Record IDs | **4,400 / 4,400 match** |
| Per-record metrics (cells, energies, isMagic, spectralCentroid) | **0 mismatches** |

No pip install was required (stdlib only).

### 8. Cross-stream findings

| Stream | Finding |
|---|---|
| **M2-S1 basis** (`S1_verify_basis.py`) | Closed-form φ_p matches Gram–Schmidt in `analyze.py`; orthonormality/Parseval independently confirmed |
| **M2-S3 controls** (`control_ensembles.py`) | Uses **Mulberry32** + configurable swap protocols — **does not reproduce** shipped control cells under seed 20260709 |
| **Shipped product** | Precomputes with Python `random.Random`; browser loads static `analysis-data.js` — internally consistent |
| **M1–M3 manager reports** | Not present at audit time; coordinator dataset audit (`coordinator_dataset_audit.json`) supports 880/7,040 counts |

**Flag for manager:** If browser-side live control regeneration is ever required, the PRNG and swap protocol must be aligned with `analyze.py`, not M2’s Mulberry32 prototype.

### 9. Commands executed

```bash
cd /Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/sub_S2
python3 scripts/basis_parseval_audit.py      # exit 0
python3 scripts/control_repro_audit.py       # exit 0
python3 scripts/full_record_scan.py          # exit 0
python3 scripts/control_cells_match.py       # exit 0
python3 scripts/evidence_table.py
bash scripts/run_all.sh                      # exit 0
```

All captured stdout in `outputs/*.txt` and structured JSON in `outputs/*.json`, `evidence/`.

---

## Files

| File | Role |
|---|---|
| `S2_report.md` | This report |
| `scripts/basis_parseval_audit.py` | 1D/2D orthonormality, Parseval, reconstruction on samples |
| `scripts/full_record_scan.py` | Exhaustive 4,400-record coefficient/Parseval/partition scan |
| `scripts/control_repro_audit.py` | Control spec, aggregation check, full pipeline repro |
| `scripts/control_cells_match.py` | Deterministic replay of all 3,520 control cell arrays |
| `scripts/evidence_table.py` | UI/numerical claims evidence table |
| `scripts/run_all.sh` | Bundled runner with logged commands |
| `outputs/basis_parseval_audit.json` | Structured basis/Parseval results |
| `outputs/basis_parseval_audit.txt` | Captured stdout |
| `outputs/control_repro_audit.json` | Control + aggregation + repro comparison |
| `outputs/control_repro_audit.txt` | Captured stdout |
| `outputs/control_cells_match.json` | 0/3520 cell mismatches |
| `outputs/control_cells_match.txt` | Captured stdout |
| `outputs/full_record_scan.json` | Zero failures across 4,400 records |
| `outputs/full_record_scan.txt` | Captured stdout |
| `outputs/repro_run/analysis.json` | Independent pipeline output |
| `outputs/run_all.log` | Timestamped full run log |
| `evidence/numerical_claims_table.json` | Counts, mode inventory, UI claim checks |
| `evidence/numerical_claims_table.txt` | Captured stdout |

---

## Acceptance Criteria Check

| Criterion | Status | Evidence |
|---|---|---|
| Audit basis orthonormality | **Done** | `basis_parseval_audit.json`; max Gram error 6.7×10⁻¹⁶ |
| Audit completeness (16-mode span) | **Done** | 2D tensor Gram = I₁₆; perfect reconstruction |
| Audit Parseval | **Done** | 0/4400 failures |
| Audit coefficient conventions | **Done** | 0/4400 coefficient mismatches; naming table in §2 |
| Audit reconstruction | **Done** | max error < 10⁻¹⁴ on samples; 0/4400 failures full scan |
| Audit control definitions | **Done** | Documented swap/random protocols from `analyze.py` |
| Audit fixed seed | **Done** | Seed 20260709 verified in metadata and repro run |
| Audit null-generation methods | **Done** | 3520/3520 control cells match deterministic replay |
| Audit sample aggregation | **Done** | `cohortSummary` recomputation exact match |
| Audit reproducibility | **Done** | Full 4400-record byte-identical metrics on repro |
| Inspect MagicMomentExplorer read-only | **Done** | `analyze.py`, `analysis.json`, `index.html`, source CSV |
| Build/run independent scripts | **Done** | 5 scripts, all exit 0 |
| Record exact commands and outputs | **Done** | `outputs/*.txt`, `run_all.log` |
| Write only in assigned folder | **Done** | No edits outside `sub_S2` |
| Do not modify MagicMomentExplorer | **Done** | Read-only access only |

---

## Questions for Manager

No questions — task was clear.

---

## Self-Assessment

**Craftsperson says:** The mathematical pipeline is internally consistent. Gram–Schmidt basis matches shipped metadata and M2’s closed form. Parseval, reconstruction, and energy partitioning hold on every record. Full pipeline reproduction with seed 20260709 is bit-exact on all reported metrics. Control cell replay confirms the null ensembles are exactly what `analyze.py` claims.

**Skeptic says:** M2’s Mulberry32 control prototype diverges from the shipped generator — any future live-regeneration feature could silently produce different nulls. The swap protocol (sequential pairing of a single `sample(16, 2k)` draw) is underspecified in user-facing docs (`README.md` referenced but not present in repo snapshot). Rounding to 8 decimals in JSON could mask tiny drift if downstream code re-derives from rounded coefficients; full scan at 10⁻⁵ tolerance still passed. M1–M3 manager reports were unavailable for integration.

**Mover says:** Core numerical claims for the shipped artifact are verified and safe to cite. The Mulberry32 mismatch is documented as a cross-stream flag, not a blocker for the static precomputed product. Shipping this audit now gives M4 concrete evidence tables and reproduction commands; deeper doc gaps can be handled in a documentation pass.

---

*Report completed 2026-07-09 by Sub-subagent 1215-M4-S2. Revised same date: corrected axial-mode list in §2 and `evidence/numerical_claims_table.*` (M12/M21 are interactions, not axial).*
