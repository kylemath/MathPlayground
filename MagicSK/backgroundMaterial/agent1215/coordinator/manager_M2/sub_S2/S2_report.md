# Numerical Verification and Low-Mode Magic-Constraint Implications

| Field | Value |
|---|---|
| **Agent** | 1215-M2-S2 |
| **Task** | Independently implement zero-/standard-library numerical checks for the centered 4×4 orthonormal tensor-product basis; verify orthogonality, completeness, Parseval; determine which low coefficients are forced to vanish by row/column (and diagonal) magic constraints; substantiate with examples and counterexamples; record numerical errors and browser tolerance implications |
| **Manager** | 1215-M2 |
| **Status** | Complete (corrected) |

---

## Work Product

### 1. Basis specification (aligned with M2-S1 and `MagicMomentExplorer/scripts/analyze.py`)

| Item | Definition |
|---|---|
| Grid | 4×4, row-major flat index `i = 4·r + c` |
| Centered coordinates | `x_c = c − 1.5`, `y_r = r − 1.5`; sample set `S = {−1.5, −0.5, 0.5, 1.5}` |
| Centered heights | `h[r,c] = G[r,c] − 8.5` (mean height of 1…16) |
| 1D inner product | `⟨f,g⟩₁ = Σ_{t∈S} f(t)g(t)` (unweighted discrete sum) |
| 1D basis | Gram–Schmidt on monomials `{1, t, t², t³}` → orthonormal `φ₀…φ₃` |
| 2D modes | `ψ_{p,q}(x_c,y_r) = φ_p(x_c)·φ_q(y_r)` — 16 tensor-product modes |
| Coefficients | `c_{p,q} = ⟨h, ψ_{p,q}⟩ = Σ_{r,c} h[r,c]·φ_p(x_c)·φ_q(y_r)` |
| Mode labels | `M_pq` with **p = x-degree (column)**, **q = y-degree (row)** |
| Parseval | `Σ_{p,q} c_{p,q}² = Σ_{r,c} h[r,c]²` (total centered energy) |

**Closed-form 1D polynomials (after Gram–Schmidt):**

| Degree | Formula on `t ∈ S` |
|---|---|
| 0 | `½` |
| 1 | `t / √5` |
| 2 | `(t² − 1.25) / 2` |
| 3 | `√(5/9)·(t³ − (41/20)t)` — equivalently sample values `[-1, 3, −3, 1] / (2√5)` |

**φ₃ verification (observed, all differences < 10⁻¹⁵):**

| `t` | Closed form | `[-1,3,−3,1]/(2√5)` | Gram–Schmidt |
|---:|---:|---:|---:|
| −1.5 | −0.223606797750 | −0.223606797750 | −0.223606797750 |
| −0.5 | +0.670820393250 | +0.670820393250 | +0.670820393250 |
| +0.5 | −0.670820393250 | −0.670820393250 | −0.670820393250 |
| +1.5 | +0.223606797750 | +0.223606797750 | +0.223606797750 |

### 2. Numerical verification results (observed)

Executed:

```bash
python3 basis_verification.py
```

| Check | Observed max error | Threshold | Result |
|---|---:|---:|---|
| φ₃ closed ≡ alt ≡ GS | < 1.942×10⁻¹⁶ | exact | **PASS** |
| 1D Gram `‖G−I‖∞` | 6.661×10⁻¹⁶ | 10⁻¹² | **PASS** |
| 16-mode Gram `‖G−I‖∞` | 7.199×10⁻¹⁶ | 10⁻¹² | **PASS** |
| All 16 mode norms `‖ψ‖²` | 1.000000000000000 | — | **PASS** |
| Reconstruction `h − Σ cψ` | 7.105×10⁻¹⁵ | 10⁻¹² | **PASS** |
| Parseval `|Σc² − Σh²|` | 2.842×10⁻¹³ | 10⁻¹² | **PASS** |
| JS float round-trip Gram | 7.199×10⁻¹⁶ | — | Basis stably orthonormal |

**Test fields:** known magic square id 1, row-only counterexample, synthetic checkerboard heights.

### 3. Low-mode constraint theory

#### 3.1 Algebraically forced (equal line sums to magic constant 34)

Write `c_{p,q} = Σ_{r,c} φ_p(x_c) φ_q(y_r) h[r,c]`.

**Column-sum constraint** (each column of raw entries sums to 34):

Pure-x modes (`q = 0`) factor:

`c_{p,0} = Σ_c φ_p(x_c) · (Σ_r h[r,c])`

Centered column margin: `Σ_r h[r,c] = col_sum_c − 4·8.5 = col_sum_c − 34`. If `col_sum_c = 34`, each term is 0.

→ **Forced:** `M10`, `M20`, `M30`.

**Row-sum constraint** (each row sums to 34): symmetric argument on `p = 0`.

→ **Forced:** `M01`, `M02`, `M03`.

**Centering:** `M00` excluded from analysis metrics (mean removed); `c₀₀ = 0` for centered heights.

#### 3.2 NOT forced by row + column sums alone

Any interaction mode (`p > 0` and `q > 0`) can survive zero row/column margins.

| Mode | Counterexample | Value |
|---|---|---:|
| `M11` | semi-magic (rows/cols = 34, diagonals ≠ 34) | −8.4 |
| `M12` | semi-magic | +10.733 |
| `M21` | semi-magic | −0.447 |
| `M22` | **synthetic margin-free field** (zero row/col sums, not a magic square) | **−1.0** |
| `M13` | semi-magic | −6.8 |
| `M31` | semi-magic | +4.2 |

**Valid row/column-only counterexample for `M22`:** synthetic field with all row and column centered margins 0 but `M22 = −1.0`. This proves zero row/column margins alone do **not** force `M22 = 0`.

**Note on semi-magic:** A semi-magic square with failing diagonals may have `M22 ≠ 0` (observed `+4.0`). That is **not** a counterexample to diagonal forcing — those diagonal relations apply only when **both** diagonals sum to 34.

#### 3.3 Diagonal constraints (main + anti diagonal sum to 34)

For centered `h` expanded in the tensor basis, with `c₀₀ = 0` and odd-degree parity `φ_p(−t) = (−1)^p φ_p(t)`:

| Diagonal balance | Relation |
|---|---|
| Main diagonal (`Σ_r h[r,r] = 0`) | `c₁₁ + c₂₂ + c₃₃ = 0` |
| Anti-diagonal (`Σ_r h[r,3−r] = 0`) | `−c₁₁ + c₂₂ − c₃₃ = 0` |

Solving the pair:

→ **`c₂₂ = 0`** (mode `M22` forced to vanish)  
→ **`c₃₃ = −c₁₁`** (mode `M33` paired with `M11`; not independently free on full magic squares)

**Observed on known full magic id 1:**

| Quantity | Value |
|---|---:|
| `c₁₁` (`M11`) | −8.6 |
| `c₂₂` (`M22`) | 0.0 |
| `c₃₃` (`M33`) | +8.6 |
| `c₁₁ + c₂₂ + c₃₃` | 0.0 |
| `−c₁₁ + c₂₂ − c₃₃` | 0.0 |

**Executable assertions (all 880 full magic squares):** `|c₁₁+c₂₂+c₃₃| < 10⁻⁹`, `|−c₁₁+c₂₂−c₃₃| < 10⁻⁹`, `|c₂₂| < 10⁻⁹`, `|c₃₃+c₁₁| < 10⁻⁹` — **ASSERT PASS**.

**Semi-magic with failing diagonals (33, 43):** balances are `c₁₁+c₂₂+c₃₃ = −1.0`, `−c₁₁+c₂₂−c₃₃ = +9.0`, `M22 = +4.0`. These violate the diagonal relations as expected; this square does **not** refute diagonal forcing.

#### 3.4 Structure across 880 normal magic squares

Batch scan of `magic_squares_880.csv` (880 full magic squares — both diagonals = 34):

| Category | Modes |
|---|---|
| **Universally zero** (max \|c\| < 10⁻⁸) | `M01`, `M02`, `M03`, `M10`, `M20`, `M30`, **`M22`** |
| **Not universally zero** | `M11`, `M12`, `M13`, `M21`, `M23`, `M31`, `M32`, `M33` |

Selected max \|c\| over 880 squares: `M11` 12.0, `M12` 17.89, `M21` 12.52, `M31` 13.8, `M33` 12.0 (= max \|M11\|, consistent with `c₃₃ = −c₁₁`).

**Interpretation:** Row/column constraints explain the six axial low modes (`M01`–`M03`, `M10`, `M20`, `M30`). **Both diagonal constraints algebraically force `M22 = 0` and `M33 = −M11` on every full magic square.** The universal `M22` vanishing on the 880-set is therefore a **theorem consequence of full magic**, not unexplained ensemble structure. Row/column constraints alone remain insufficient to force `M22` (synthetic counterexample `M22 = −1`).

#### 3.5 One-sided constraint counterexamples

| Square | Row=34 | Col=34 | `M10` | `M01` | `M30` | `M03` |
|---|---|---|---:|---:|---:|---:|
| Row-only partition | ✓ | ✗ | +15.21 | ~0 | −5.37 | ~0 |
| Col-only (transpose) | ✗ | ✓ | ~0 | +15.21 | ~0 | −5.37 |

Confirms: column constraint forces `M10,M20,M30`; row constraint forces `M01,M02,M03`; violating one side revives the corresponding axial modes.

**Note:** `M20 = 0` in the row-only example is **incidental cancellation** for the symmetric row-block partition, not a row-sum theorem.

### 4. Browser `Number` (IEEE-754) tolerance guidance

| Use case | Recommended tolerance | Rationale |
|---|---:|---|
| Orthogonality / Gram check | **10⁻¹⁰** | Observed Gram error ~7×10⁻¹⁶; allow headroom for 16-term accumulation in client |
| Coefficient "exactly zero" (display) | **10⁻⁸** | Matches `analyze.py` 8-decimal rounding |
| UI zero badge / constraint flag | **10⁻⁶** | Conservative for chained ops (coeff → energy → aggregation) |
| Parseval / reconstruction audit | **10⁻¹⁰** | Safe for precomputed JSON; offline Python at ~10⁻¹⁴ |
| Diagonal balance checks | **10⁻⁹** | Observed full-magic balances at ~10⁻¹⁵ |
| Integer line-sum checks | **exact** | Row/col/diag sums are integers; compare with `=== 34` |

**Implementation notes for zero-dependency JS:**

1. Precompute `BASIS` once; values match S1 JSON to ~10⁻¹⁵.
2. Use the same coefficient loop as Python: `Σ h[r,c]·BASIS[p][c]·BASIS[q][r]`.
3. When testing forced zeros on magic squares, treat \|c\| < 10⁻⁸ as 0 for parity with Python output.
4. Do **not** use `c === 0` for constraint detection; use thresholded tests.
5. Energy sums (`c²`) accumulate ~15 interaction modes; expect ~10⁻¹² relative drift — acceptable for ranking, not for exact equality.

### 5. Low-mode summary table

| Mode | Degree | Forced by col=34 | Forced by row=34 | Forced by both diag=34 | Universal on 880 full magic |
|---|---|---|---|---|---|
| M00 | 0 | centering | centering | — | yes (excluded) |
| M10 | 1 | **yes** | no | no | yes |
| M01 | 1 | no | **yes** | no | yes |
| M20 | 2 | **yes** | no | no | yes |
| M02 | 2 | no | **yes** | no | yes |
| M30 | 3 | **yes** | no | no | yes |
| M03 | 3 | no | **yes** | no | yes |
| M11 | 2 | no | no | no | **no** |
| M22 | 4 | no | no | **yes** (`c₂₂=0`) | yes |
| M33 | 6 | no | no | **paired** (`c₃₃=−c₁₁`) | no (varies with M11) |
| M12,M21,M13,M31,… | mixed | no | no | no | no |

---

## Files

| File | Description |
|---|---|
| `S2_report.md` | This report |
| `basis_verification.py` | Standard-library verification: Gram–Schmidt basis, φ₃ equivalence assertions, 16-mode checks, constraint counterexamples, diagonal-balance assertions on 880 squares |
| `verification_output.txt` | Console transcript from `python3 basis_verification.py` |
| `verification_output.json` | Machine-readable results, tolerances, theory flags, batch-scan statistics |

---

## Acceptance Criteria Check

| # | Criterion | Status |
|---|---|---|
| 1 | Runnable Python standard-library script and observed output artifact | **Met** — `basis_verification.py`; `verification_output.txt` / `.json` |
| 2 | Verify all 16 modes, Gram-matrix error, completeness/reconstruction, Parseval numerically | **Met** — §2; all PASS at 10⁻¹² thresholds |
| 3 | Test known 4×4 magic square; analyze low modes with counterexamples | **Met** — §3; row-only, col-only, semi-magic (diag-fail illustration), synthetic margin-free `M22` counterexample |
| 4 | Report tolerances appropriate to browser Number arithmetic | **Met** — §4 |
| 5 | Produce `S2_report.md` and artifacts in assigned folder | **Met** |
| 6 | Correct φ₃ closed form and diagonal-constraint analysis | **Met** — §1, §3.3; executable assertions in script §0, §7b, §8, §9 |

---

## Questions for Manager

No questions — task was clear.

---

## Self-Assessment

**Craftsperson says:** The corrected φ₃ closed form `√(5/9)·(t³−(41/20)t)` matches Gram–Schmidt and the rational sample values `[-1,3,−3,1]/(2√5)` to machine precision. Diagonal balance on full magic squares is now stated correctly: `c₁₁+c₂₂+c₃₃=0` and `−c₁₁+c₂₂−c₃₃=0` imply `c₂₂=0` and `c₃₃=−c₁₁`, verified by assertions on all 880 squares. The row/column-only `M22` counterexample (`M22=−1` on zero margins) is retained and distinguished from the semi-magic illustration, which merely shows what happens when diagonal constraints are absent.

**Skeptic says:** The diagonal derivation is stated as fact but not fully expanded step-by-step in this report — a reader may want the explicit contraction along main/anti diagonals using `φ_p(−t)=(−1)^p φ_p(t)`. The semi-magic square is useful only as a diag-fail illustration; it must not be misread as evidence against diagonal forcing. Browser tolerances remain extrapolated from Python struct round-trip, not a live Node harness. Whether `c₃₃=−c₁₁` has further combinatorial consequences for normal-magic enumeration is outside this verification scope.

**Mover says:** Ship the corrected six-axial + diagonal-forced-`M22` taxonomy as the integration baseline. Treat semi-magic `M22≠0` as expected behavior under absent diagonal constraints, not as a theorem counterexample. Downstream agents can rely on executable assertions in `basis_verification.py` and the updated summary table without treating `M22` as unexplained empirical structure.

---

*Report generated 2026-07-09 by Agent 1215-M2-S2.*
