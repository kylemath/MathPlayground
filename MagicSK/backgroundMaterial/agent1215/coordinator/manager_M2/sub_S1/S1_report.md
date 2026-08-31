# 4×4 Centered Orthonormal Moment Basis — Mathematical Specification

## Metadata

| Field | Value |
|-------|-------|
| **Agent** | 1215-M2-S1 |
| **Task** | Derive explicit centered coordinates, complete 16-mode tensor-product orthonormal spatial basis, inner product, coefficient formula, Parseval identity, centering/scaling, degree/order grouping, documented “higher moments” ordering, and unambiguous retained/residual energy denominators; verify numerically; assess browser-JS feasibility |
| **Manager** | 1215-M2 |
| **Status** | Complete |

---

## Work Product

### Summary

Delivered a self-contained mathematical specification for spatial moment analysis on a 4×4 grid, suitable for zero-dependency browser JavaScript and independent Python verification.

**Centered coordinates:** \(x_i = y_j = i - \tfrac{3}{2} \in \{-\tfrac{3}{2}, -\tfrac{1}{2}, \tfrac{1}{2}, \tfrac{3}{2}\}\).

**Inner product (primary):** uniform **sum-weight** \(\langle f,g\rangle_{\Sigma} = \sum_{i,j} f_{ij} g_{ij}\) — a valid convention; all coefficients and energies below use it.

**Mean-weight bridge:** some implementations use \(\langle f,g\rangle_{\mu} = \frac{1}{16}\sum f_{ij}g_{ij}\) with basis \(\Phi_{pq} = 4\Psi_{pq}\) (equivalently \(\psi_p = 2\varphi_p\) per axis). Conversion: \(\tilde{c}_{pq} = c_{pq}/4\); \(\|f\|_{\mu}^{2} = \|f\|_{\Sigma}^{2}/16\); \(\tilde{c}_{00}=\mu\) while \(c_{00}=4\mu\).

**1D orthonormal basis** (Gram–Schmidt on \(\{1,t,t^2,t^3\}\)):

| \(p\) | \(\varphi_p(t)\) |
|-------|------------------|
| 0 | \(\tfrac{1}{2}\) |
| 1 | \(t/\sqrt{5}\) |
| 2 | \((t^2 - \tfrac{5}{4})/2\) |
| 3 | \(\sqrt{\tfrac{5}{9}}\,(t^3 - \tfrac{41}{20}t)\) |

**2D modes:** \(\Psi_{pq}(i,j) = \varphi_p(x_i)\varphi_q(y_j)\), 16 orthonormal modes.

**Coefficients / reconstruction:**

\[
c_{pq} = \sum_{i,j} f_{ij}\varphi_p(x_i)\varphi_q(y_j), \qquad
f_{ij} = \sum_{p,q} c_{pq}\varphi_p(x_i)\varphi_q(y_j)
\]

**Parseval:** \(\|f\|^2 = \sum_{p,q} c_{pq}^2\).

**“Higher moments” (selected subset):** 13 modes with total degree \(p+q \ge 2\), ordered by `(p+q, max(p,q), p, q)`. Distinct from the complete 16-mode basis. Affine subset \(\mathcal{A}=\{(p,q):p+q\le 1\}\) has **3 modes**: \((0,0),(0,1),(1,0)\).

**Energy denominators (explicit):**

- \(E_{\text{total}} = \sum c_{pq}^2\), \(E_{\text{dc}} = c_{00}^2\), \(E_{\text{nonconst}} = E_{\text{total}} - E_{\text{dc}}\)
- \(E_{\text{retained}}(S) = \sum_{(p,q)\in S} c_{pq}^2\), \(E_{\text{residual}}(S) = E_{\text{total}} - E_{\text{retained}}(S)\)
- Fractions always label numerator **and** denominator; `retained_frac_nonconst` excludes DC from numerator when \((0,0)\in S\); constant-field \(E_{\text{nonconst}}=0\) → safe ratio **0**.

**Numerical verification (Python `S1_verify_basis.py`):** orthogonality \(<10^{-16}\), Parseval \(<10^{-12}\), reconstruction \(<10^{-14}\), magic-square \(E_{\mathcal{H}} = E_{\text{nonconst}} = 340\).

**Browser feasibility:** confirmed via `S1_basis.js` (Float64Array, precomputed modes, no dependencies). Critical: \(\varphi_3\) must use the Gram–Schmidt formula, not raw \(t^3\).

### Key finding flagged for manager

An initial closed form \(\varphi_3 \propto t^3\) was **wrong** — it breaks orthogonality to \(\varphi_1\) because \(\sum t^{4} = 41/4\) makes \(\langle t^{3}, \varphi_{1}\rangle \neq 0\). Corrected form removes the \(\varphi_{1}\) component: \(\varphi_3 \propto t^{3} - \tfrac{41}{20}t\). (A separate earlier typo had mislabeled \(\sum t^{2}\) as \(41/4\); the correct value is **5**, giving \(c=5/4\) in the degree-2 Gram–Schmidt step.) All downstream artifacts use the corrected basis.

---

## Files

| File | Description |
|------|-------------|
| `S1_report.md` | This report |
| `S1_basis_derivation.md` | Full mathematical derivation, all 16 modes, energy conventions, tolerances |
| `S1_verify_basis.py` | Runnable independent checks (orthogonality, Parseval, reconstruction, edge cases) |
| `S1_verify_output.json` | Captured output from verification script |
| `S1_basis.js` | Zero-dependency browser reference implementation |
| `S1_modes_table.json` | Precomputed 16 mode vectors, ordering, formulas (machine-readable) |
| `S1_verification_results.json` | Extended numerical results including magic-square coefficients |

---

## Acceptance Criteria Check

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Explicit coordinates, inner product weighting, orthonormal 1D and 2D bases, all 16 modes, coefficients, inverse reconstruction, Parseval | **Met** | `S1_basis_derivation.md` §1–6 (sum-weight primary; mean-weight bridge in §2); `S1_modes_table.json`; `S1_verify_basis.py` PASS |
| 2 | Explicit centering/scaling and total/nonconstant energy denominator conventions, including constant-field edge cases | **Met** | `S1_basis_derivation.md` §7, §10; constant-field check in verify script |
| 3 | Distinguish complete basis from selected higher-mode order; define retained/residual energy without ambiguity | **Met** | §8–9 (complete vs \(\mathcal{H}\)); §10 partition identities and fraction table |
| 4 | Browser-feasible formulas and recommended tolerances | **Met** | `S1_basis.js`; §11 tolerance table |
| 5 | Produce `S1_report.md` plus at least one detailed mathematical artifact | **Met** | This report + `S1_basis_derivation.md` |

---

## Questions for Manager

No questions — task was clear.

One **reconciliation note** (not blocking): final cell indexing convention (row-major vs column-major) should be aligned with M1’s canonical CSV layout when that stream lands. This spec uses row-major `k = 4i + j`, consistent with the coordinator dataset audit scripts.

---

## Self-Assessment

**Craftsperson says:** The derivation is complete and numerically verified. Closed-form 1D basis functions, explicit 16-mode tensor products, Parseval, sum/mean-weight conversion table, and energy partitions are implementable in plain JS. Degree-2 arithmetic is now explicit (\(\sum t^{2}=5\Rightarrow c=5/4\)); affine block \(\mathcal{A}\) is correctly 3 modes.

**Skeptic says:** Sum-weight vs mean-weight is a convention choice — both are valid if conversion factors are applied consistently. Degree-\(\ge 2\) “higher moments” remains a project convention. Magic-square linear-mode zeros are empirical (symmetry), not enforced by definition. M1 CSV index ordering must be confirmed before production embedding.

**Mover says:** Ship the corrected documentation now; verification script unchanged and still PASS. Manager can integrate using either weight convention via the \(4\times\) basis / \(\tilde{c}=c/4\) / \(E_{\mu}=E_{\Sigma}/16\) bridge. Index alignment with M1 can be patched without changing basis math.

---

*Report generated 2026-07-09 by Agent 1215-M2-S1*
