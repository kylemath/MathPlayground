# Deterministic Control Ensembles and Statistical Summaries for 4×4 Grids

| Field | Value |
|---|---|
| **Agent** | 1215-M2-S3 |
| **Task** | Define and exercise reproducible random-permutation controls and sequential 1/2/3 transposition perturbations for 4×4 grids; specify RNG, sampling protocols, statistical design, browser parity, and moment-energy summaries |
| **Manager** | 1215-M2 |
| **Status** | Complete (deterministic-design correction pass) |

---

## Work Product

### 1. Scope and grid encoding

- **Grid:** 4×4 array of distinct values (typically permutation of 1…16), stored **row-major** as flat index `i = 4·r + c` for row `r`, column `c` (`r,c ∈ {0,1,2,3}`).
- **Cell positions:** 16 indices; **120 unordered distinct pairs** `(a,b)` with `0 ≤ a < b < 16`.
- **Transposition:** swap values at two distinct cells; pairs are **unordered**; **no-ops** `(a,a)` are **forbidden**.

### 2. Seeded RNG (deterministic, browser-compatible)

| Item | Specification |
|---|---|
| Algorithm | **Mulberry32** on **uint32** state |
| State init | `state = u32(seed)`; if `0`, replace with `1` |
| Raw output | `raw = u32(…mix…) ∈ {0,…,2³²−1}` from `mulberry32_next_u32` |
| Float (optional) | `u = raw / 2³² ∈ [0,1)` — **not** used for integer draws |
| **Integer draw `randBelow(n)`** | **Rejection sampling on raw uint32:** `limit = ⌊2³²/n⌋·n`; repeat draw until `raw < limit`; return `raw mod n`. Exact uniform on `{0,…,n−1}` under the PRNG model. |
| Replicate seed | `deriveReplicateSeed(baseSeed, squareId, replicate, domain)` = `u32(u32(baseSeed) ⊕ u32(squareId·0x9E3779B1) ⊕ u32(replicate·0x85EBCA77) ⊕ domain)`, zero forbidden |
| **Domain tags** | `PERM_DOMAIN = 0x5065524D` ("PeRM"); `SWAP_DOMAIN = 0x53574150` ("SWAP") |
| Default base seed | `1215` (configurable) |

**Why not `floor(u·n)`?** Mapping a float `u ∈ [0,1)` via `floor(u·n)` introduces **modulo bias** unless `n` divides `2³²`. For Fisher–Yates at `n = 16` the bias vanishes (16 | 2³²), but pair draws use `n = 120` (120 ∤ 2³²) and rejection steps in swap sampling also depend on unbiased `randBelow`. The corrected implementation uses rejection on raw uint32 in both Python and JavaScript.

**Why not Python `random`?** Mersenne Twister is not trivially replicated in zero-dependency JavaScript. Mulberry32 is small, fast, and **bit-identical** on uint32 paths in `control_ensembles.py` and `control_ensembles.js`.

### 3. Unbiased random permutations (Fisher–Yates)

**Algorithm (Knuth shuffle):** For array length `n`, for `i = n−1 … 1`, draw `j ~ Uniform{0,…,i}` via rejection-sampled `randBelow` and swap `A[i]`, `A[j]`.

**Properties:**
- **Exact** uniform over `n!` permutations when each `j` is exactly uniform (guaranteed here by rejection `randBelow`).
- **Condition `rand`:** apply Fisher–Yates to a **copy of the supplied base square's value multiset** (`base_flat.slice()` / `list(base_flat)`), independently per replicate on the **permutation domain stream**. Does **not** preserve magic constraints. Hardcoding `1…16` is reserved only for tests that explicitly assert a normal-square input template.

**RNG independence:** `rand` consumes `PERM_DOMAIN`; swap arms consume `SWAP_DOMAIN`. Same `(squareId, replicate)` index links arms, but **bitstreams are domain-separated** — claims of independence between permutation and swap controls are true under the PRNG model.

**Determinism check (observed, square id 1, rep 0, seed 1215):** shuffled base head `[4,8,13,11,14,12,3,15]` — identical in Python and Node (`parity_check.mjs`).

### 4. Sequential k-swap protocols (k = 1, 2, 3)

#### 4.1 Definitions

| Term | Definition |
|---|---|
| **Swap step** | One transposition of values at unordered pair `(a,b)`, `a≠b` |
| **Sequential k-perturbation** | Start from base square `G₀`; apply swaps `τ₁,…,τ_k` in order to obtain `G_k` |
| **Pair universe** | Fixed enumeration `UNORDERED_PAIRS` of all 120 pairs with `a < b` (index `0…119`) |

#### 4.2 Pair-sampling modes (configurable)

| Mode ID | Each step draws… | Shared cells across steps? | Repeated pair in same replicate? | Immediate direct undo? |
|---|---|---|---|---|
| **`distinct_pairs_no_replacement`** *(production default)* | Uniform among pairs not yet used in this replicate (rejection over 120) | **Allowed** | **Forbidden** within k | **Forbidden** (pair already used) |
| **`uniform_with_replacement`** | Uniform on all 120 pairs | Allowed | Allowed (prob ≈ 1/120) | Allowed (prob ≈ 1/120) |
| **`no_immediate_undo`** | Uniform on 120, reject if equals previous step's pair | Allowed | Allowed except consecutive duplicate | **Forbidden** |
| **`distinct_pairs_no_immediate_undo`** | Uniform among unused pairs, also reject immediate undo | Allowed | **Forbidden** within k | **Forbidden** |

**No-ops:** always forbidden at draw time (only unordered pairs with `a < b` are in the universe).

**Production default policy:** `distinct_pairs_no_replacement` + `paired_prefix`.

**What the default does *not* forbid (documented explicitly):**
- **Shared cells** across different pairs within a replicate (e.g. `(0,1)` then `(1,2)`).
- **Indirect path collisions** — different swap sequences that yield the same grid.
- **Reduced Hamming distance** — a later swap may undo an *earlier* cell change via a different pair (not immediate direct undo of the same unordered pair).

Controls are a **transposition random walk** uniform over **ordered swap steps** under the chosen pair-sampling mode, **not** uniform over reachable grids.

#### 4.3 Relation of samples across k (paired vs independent)

| Design | How SWAP1, SWAP2, SWAP3 relate | Use when |
|---|---|---|
| **`paired_prefix`** *(production default)* | One **swap-domain** RNG stream per replicate; swaps `τ₁,τ₂,τ₃` drawn once; SWAPk uses **first k swaps** on the **same** base square | Comparing k on a **matched** perturbation path; lower variance for incremental effects |
| **`independent_resample`** | Separate fresh k-swap sequences per k (same seed family, different consumption) | Need **marginal** distributions at each k without path coupling |

**Random permutations (`rand`):** always on a **separate domain stream** from swaps; independent of swap bit consumption.

#### 4.4 Aggregation across replicates and squares

**Two-level hierarchy:**

| Level | Population | Statistics | Uncertainty interpretation |
|---|---|---|---|
| **L1 — Monte Carlo within square** | `B` replicates per `(squareId, condition)` | `μ_s`, `σ_s`, q05/q50/q95 of metric | MC noise; SE(mean) `≈ σ_s/√B` |
| **L2 — Across source squares** | 880 magic squares | Mean/median/std of `{μ_s}`; optionally pool with square weights | Heterogeneity across squares; **do not** confuse `std(μ_s)` with MC error |

**Within-square (per condition):**

| Statistic | Definition |
|---|---|
| Mean | `μ_s = (1/B) Σ m_b` over replicates `b = 1…B` |
| Std (reporting) | Population std `σ_s = sqrt(Σ(m_b−μ_s)²/B)` (script default) |
| Quantiles | Linear interpolation on **sorted** replicate values: q05, q50, q95 |
| Paired deltas (`paired_prefix`) | Per replicate: `Δ₂₁ = residual₂ − residual₁`, `Δ₃₂ = residual₃ − residual₂`; summarize mean/std/quantiles |

**Across-square grand mean** (example for deployment):

- `μ̄ = (1/880) Σ_s μ_s`
- MC contribution to uncertainty: `σ_MC² ≈ mean_s(σ_s²/B)`
- Between-square contribution: `σ_sq² = Var_s(μ_s)`
- Combined SE: `SE(μ̄) ≈ sqrt(σ_MC² + σ_sq²/880)` when squares are i.i.d. summaries

**Multiple conditions:** treat `rand`, `swap1`, `swap2`, `swap3` as **four parallel control arms** per square. Compare magic-square baseline (zero swaps) to control distributions; do **not** pool across arms without labeling.

### 5. Recommended and configurable sample sizes

| Setting | Smoke / dev | Production (recommended) | Configurable range | Notes |
|---|---|---|---|---|
| Replicates per square per condition `B` | **200** | **2000** | 50–5000 | See justification below |
| Base seed | **1215** | **1215** | any uint32 | Document in dataset manifest |
| Retain cutoff degree | **1** | **1** | 0…6 | Retained energy = Σ degree ≤ d; residual = total − retained |
| Swap mode | `distinct_pairs_no_replacement` | same | see §4.2 | `uniform_with_replacement` for sensitivity only |
| Across-k design | `paired_prefix` | same | or `independent_resample` | Report which was used |

**Production `B = 2000` justification:**
- Typical within-square residual σ ≈ 1–2 energy units; target MC standard error `σ/√B ≤ 0.05` ⇒ `B ≥ 1600`; 2000 provides headroom.
- Tail quantiles (q05/q95) at 5% nominal level need `B·p ≥ 10` rule-of-thumb ⇒ `B ≥ 200`; 2000 stabilizes tails for per-square JSON manifests.
- Offline cost: 880 squares × 4 arms × 2000 ≈ **7.04M** grid evaluations — feasible for batch precompute; browser spot checks stay at `B ≤ 200`.

**Smoke `B = 200`:** fast CI artifact (`simulation_output.json`); adequate for parity and pipeline wiring, not for publication tails.

**Uncertainty reporting:** Store **mean, std, q05, q50, q95** per metric per arm per square. Optional normal-approx CI for within-square mean: `μ_s ± 1.96·σ_s/√B`. Report across-square spread of `μ_s` separately.

### 6. Bias and coverage implications

| Issue | Implication | Mitigation |
|---|---|---|
| **`floor(u·n)` integer bias** | Non-uniform Fisher–Yates / pair index when n ∤ 2³² | **Fixed:** rejection `randBelow` on raw uint32 |
| **`distinct_pairs_no_replacement`** | No repeated pair identity; no immediate direct undo; shared cells still allowed | Production default; document path collisions / Hamming reductions as allowed |
| **Paired prefix across k** | SWAP1 distribution is **not** the marginal of SWAP2/3; coupled paths | Correct for incremental-swap narrative; use `independent_resample` for uncoupled marginals |
| **`rand` vs swaps** | Random permutations destroy spatial structure; swap arms preserve value multiset | Separate domain streams; compare each arm to magic baseline |
| **120-pair uniform steps** | Not uniform over **grids**; uniform over **ordered swap steps** under mode | State clearly in reports and UI |
| **Small B** | Quantile noise for B < 500 | Use B = 2000 for production manifests |
| **Moment basis alignment** | Retained/residual split depends on orthonormal basis (Gram–Schmidt on 4×4 centered coords) | Reconcile cutoff with M2 S1/S2 basis doc; Parseval checked to ~0 |

**Coverage:** With `distinct_pairs_no_replacement` and k ≤ 3, reachable grids remain near base in Hamming distance (each swap changes two cells); does **not** cover full value-permutation space (unlike `rand`).

### 7. Moment–energy tie-in (retained / residual)

**Coordinates:** `x_c = c − 1.5`, `y_r = r − 1.5`.

**Basis:** 1D orthonormal polynomials on `{−1.5,−0.5,0.5,1.5}` via Gram–Schmidt (degrees 0…3); 2D modes `ψ_{p,q}(x,y) = φ_p(x)φ_q(y)`; **16 modes**, ordered by total degree `p+q`.

**Coefficients:** `c_{p,q} = (1/16) Σ_{r,c} G[r,c] · ψ_{p,q}(x_c,y_r)`.

**Energies:**
- **Total:** `E_total = Σ c_{p,q}²` (equals mean square of cell values — Parseval verified)
- **Retained (degree ≤ d*):** `E_ret = Σ_{p+q ≤ d*} c_{p,q}²`
- **Residual:** `E_res = E_total − E_ret`

**Observed on magic square id 1** (d* = 1, smoke B = 200, `distinct_pairs_no_replacement`, `paired_prefix`, domain-separated RNG):

| Condition | mean E_res | q05 | q50 | q95 |
|---|---:|---:|---:|---:|
| baseline (0 swaps) | 21.25 | — | — | — |
| rand | 18.58 | 14.54 | 19.20 | 21.04 |
| swap1 | 20.59 | 18.97 | 20.94 | 21.24 |
| swap2 | 20.08 | 17.42 | 20.51 | 21.22 |
| swap3 | 19.64 | 16.23 | 20.04 | 21.14 |

**Interpretation:** Random permutations lower residual low-degree energy structure relative to this magic square; 1–3 distinct-pair swaps slightly **mix** retained/residual partition while preserving total energy (total energy invariant under value relabeling — constant 93.5 for any permutation of the same multiset).

Paired deltas: mean `Δ(swap2−swap1) ≈ −0.51`, `Δ(swap3−swap2) ≈ −0.44` on residual energy for square 1.

### 8. Zero-dependency browser JavaScript parity

`control_ensembles.js` exports:

- `mulberry32Next`, `mulberry32NextU32`, `seedToState`, `randBelow`, `deriveReplicateSeed`
- `PERM_DOMAIN`, `SWAP_DOMAIN`
- `fisherYates`, `swapEnsembleForKValues`
- `energyMetrics`, `runControlEnsemble`

**Matching rules:**
1. Use **uint32** arithmetic (`>>> 0` in JS; `& 0xFFFFFFFF` in Python).
2. **Rejection `randBelow`** on raw uint32 with identical `limit` arithmetic.
3. Share identical `UNORDERED_PAIRS` enumeration (nested loops `i < j`).
4. Same `deriveReplicateSeed` mixing constants and domain tags.
5. Same Fisher–Yates loop direction (`i = n−1 … 1`).
6. Same production default: `distinct_pairs_no_replacement` + `paired_prefix`.
7. `rand` shuffles **base multiset**; swap arms use **swap domain** only.

**Parity verification (`parity_check.mjs`, 2026-07-09):**

| Anchor | Python | Node | Match |
|---|---:|---:|:---:|
| `first_rand_perm_head` | `[4,8,13,11,14,12,3,15]` | same | ✓ |
| `swap1_residual_rep0` | 21.246875 | 21.246875 | ✓ |
| `mean_residual` swap1 (B=200) | 20.586016 | 20.586016 | ✓ |

**Deployment pattern:** Precompute summaries offline with Python at `B = 2000`; ship JSON per square. Optional client-side `runControlEnsemble` for spot checks (keep B ≤ 200 on main thread).

### 9. Runnable verification

Executed:

```bash
python3 control_ensembles.py
node parity_check.mjs
```

Artifacts: `simulation_output.json`, `simulation_output.txt`, `parity_check.mjs`.

---

## Files

| File | Description |
|---|---|
| `S3_report.md` | This report |
| `control_ensembles.py` | Standard-library Python: Mulberry32, rejection `randBelow`, domain-separated streams, Fisher–Yates, swap protocols, moment energy, demo runner |
| `control_ensembles.js` | Zero-dependency browser module with matching algorithms |
| `parity_check.mjs` | Node parity anchors vs Python output |
| `simulation_output.json` | Machine-readable smoke output (square id 1, B=200) |
| `simulation_output.txt` | Console transcript from demo run |

---

## Acceptance Criteria Check

| # | Criterion | Status |
|---|---|---|
| 1 | Fully specify seed/RNG and unbiased random-permutation generation | **Met** — §2–3; rejection `randBelow`; Fisher–Yates exact under PRNG model; domain-separated streams |
| 2 | Fully specify sequential 1/2/3 swap protocols: distinct pairs, shared elements, no-op/repeat/undo policies, aggregation | **Met** — §4; production default `distinct_pairs_no_replacement`; path-collision policy documented |
| 3 | Define recommended and configurable sample sizes, paired design, uncertainty summaries, quantiles, multiple-condition handling | **Met** — §5–6; smoke B=200, production B=2000; two-level aggregation |
| 4 | Produce runnable Python standard-library simulation/check script and observed output | **Met** — `control_ensembles.py`; `simulation_output.*` |
| 5 | Discuss exact matching implementation in zero-dependency browser JavaScript | **Met** — §8; `control_ensembles.js`; `parity_check.mjs` verified |
| 6 | Produce S3_report.md and artifacts in assigned folder | **Met** |

---

## Questions for Manager

No questions — task was clear.

---

## Self-Assessment

**Craftsperson says:** The correction pass is structurally sound: rejection-sampled `randBelow` removes modulo bias on n = 120 pair draws; domain tags make permutation/swap independence claims true; production defaults (`distinct_pairs_no_replacement`, `paired_prefix`) match the manager spec; Python and Node agree on all parity anchors.

**Skeptic says:** Moment basis normalization and retain cutoff (`degree ≤ 1`) remain **locally derived** until sibling M2 agents finalize the coordinator `moments.md`. `distinct_pairs_no_replacement` still allows indirect cell re-collisions and reduced Hamming distance — correctly documented, but downstream UI copy must not over-promise "strictly increasing Hamming distance." Production B = 2000 is justified heuristically, not from a formal power analysis.

**Mover says:** Ship smoke artifacts at B = 200 for wiring, production manifests at B = 2000 with the corrected defaults, and treat `uniform_with_replacement` as an explicit sensitivity flag only. Parity is verified; M3/M4 can integrate without waiting on further S3 iteration.

---

*Report generated 2026-07-09 by Agent 1215-M2-S3 (deterministic-design correction pass).*
