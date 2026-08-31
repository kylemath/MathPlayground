# S1 — Mathematical Derivation: 4×4 Centered Orthonormal Moment Basis

**Agent:** 1215-M2-S1  
**Date:** 2026-07-09

---

## 1. Grid indexing and centered coordinates

Let cell indices be `(i, j)` with `i, j ∈ {0, 1, 2, 3}`:

| Index | Meaning |
|-------|---------|
| `i` | row, top → bottom |
| `j` | column, left → right |
| linear | `k = 4i + j` (row-major, `k ∈ {0,…,15}`) |

**Centered coordinates** (origin at grid center):

\[
x_i = i - \tfrac{3}{2},\qquad y_j = j - \tfrac{3}{2}
\]

Explicit values:

| index | 0 | 1 | 2 | 3 |
|-------|---|---|---|---|
| \(x_i\) or \(y_j\) | \(-\tfrac{3}{2}\) | \(-\tfrac{1}{2}\) | \(\tfrac{1}{2}\) | \(\tfrac{3}{2}\) |

---

## 2. Inner product and weighting

### Primary convention: sum-weight (this document)

Use the **uniform discrete inner product** with weight 1 at each of the 16 cells:

\[
\langle f, g \rangle_{\Sigma} = \sum_{i=0}^{3}\sum_{j=0}^{3} f_{ij}\, g_{ij}
\]

\[
\|f\|_{\Sigma}^{2} = \langle f, f \rangle_{\Sigma} = \sum_{i,j} f_{ij}^{2}
\]

This is a **valid, fully consistent convention**: orthonormal bases, coefficients, and Parseval are all defined with respect to the same measure. No quadrature weights are needed on equispaced nodes.

**Rationale:** sum-weighting is browser-trivial and matches the coordinator’s “zero-dependency JS” requirement.

### Equivalent mean-weight convention (some implementations)

An equally valid convention uses the **mean inner product**

\[
\langle f, g \rangle_{\mu} = \frac{1}{16}\sum_{i,j} f_{ij}\, g_{ij},
\qquad
\|f\|_{\mu}^{2} = \frac{1}{16}\sum_{i,j} f_{ij}^{2}.
\]

**Bridge:** define scaled 1D factors \(\psi_{p}(t) = 2\,\varphi_{p}(t)\) and 2D modes

\[
\Phi_{pq}(i,j) = \psi_{p}(x_{i})\,\psi_{q}(y_{j}) = 4\,\Psi_{pq}(i,j).
\]

Then \(\{\Phi_{pq}\}\) is orthonormal under \(\langle\cdot,\cdot\rangle_{\mu}\), and coefficients/energies convert uniformly:

| Quantity | Sum-weight \((\Psi,\langle\cdot,\cdot\rangle_{\Sigma})\) | Mean-weight \((\Phi,\langle\cdot,\cdot\rangle_{\mu})\) |
|----------|----------------------------------------------------------|----------------------------------------------------------|
| Basis mode | \(\Psi_{pq}\) | \(\Phi_{pq} = 4\,\Psi_{pq}\) |
| Coefficient | \(c_{pq} = \langle f,\Psi_{pq}\rangle_{\Sigma}\) | \(\tilde{c}_{pq} = \langle f,\Phi_{pq}\rangle_{\mu} = c_{pq}/4\) |
| Reconstruction | \(f = \sum c_{pq}\Psi_{pq}\) | \(f = \sum \tilde{c}_{pq}\Phi_{pq}\) (identical field values) |
| Parseval / energy | \(\|f\|_{\Sigma}^{2} = \sum c_{pq}^{2}\) | \(\|f\|_{\mu}^{2} = \sum \tilde{c}_{pq}^{2} = \|f\|_{\Sigma}^{2}/16\) |
| DC coefficient | \(c_{00} = 4\mu\) | \(\tilde{c}_{00} = \mu\) |

All formulas below use **sum-weight** unless explicitly labeled \(\mu\).

---

## 3. One-dimensional orthonormal basis (Gram–Schmidt)

Apply Gram–Schmidt to monomials \(\{1, t, t^{2}, t^{3}\}\) on the four nodes \(t \in \{- \tfrac{3}{2}, -\tfrac{1}{2}, \tfrac{1}{2}, \tfrac{3}{2}\}\).

### Degree 0

\[
\|1\|^{2} = 4 \quad\Rightarrow\quad \varphi_{0}(t) = \tfrac{1}{2}
\]

### Degree 1

\(\langle t, 1\rangle = 0\) by symmetry.

\[
\|t\|^{2} = 2\bigl(\tfrac{9}{4}+\tfrac{1}{4}\bigr) = 5
\quad\Rightarrow\quad
\varphi_{1}(t) = \frac{t}{\sqrt{5}}
\]

### Degree 2

Let \(v(t) = t^{2} - c\). Orthogonality to \(\varphi_{0}\) requires \(\langle t^{2} - c, 1\rangle = 0\), i.e. \(c\,\langle 1,1\rangle = \langle t^{2}, 1\rangle\).

At the four nodes, \(t^{2} \in \{\tfrac{9}{4}, \tfrac{1}{4}, \tfrac{1}{4}, \tfrac{9}{4}\}\), so

\[
\langle t^{2}, 1\rangle = \sum t^{2} = 5,
\qquad
\langle 1, 1\rangle = 4
\;\Rightarrow\;
c = \tfrac{5}{4}.
\]

(Note: \(\sum t^{4} = \tfrac{41}{4}\) is a **different** quantity, used in the degree-3 step below.)

Check \(\langle t^{2} - \tfrac{5}{4}, t\rangle = 0\) (odd symmetry). Then:

\[
\|t^{2} - \tfrac{5}{4}\|^{2} = 4
\quad\Rightarrow\quad
\varphi_{2}(t) = \frac{t^{2} - \tfrac{5}{4}}{2} = \frac{4t^{2} - 5}{8}
\]

### Degree 3

Start with \(t^{3}\). By symmetry \(\langle t^{3}, 1\rangle = 0\) and \(\langle t^{3}, t^{2}-\tfrac{5}{4}\rangle = 0\).

\[
\langle t^{3}, \varphi_{1}\rangle = \frac{1}{\sqrt{5}}\sum t^{4} = \frac{41}{4\sqrt{5}}
\]

Gram–Schmidt residual:

\[
w(t) = t^{3} - \frac{41}{20}\,t
\]

\[
\|w\|^{2} = \frac{9}{5}
\quad\Rightarrow\quad
\varphi_{3}(t) = \sqrt{\tfrac{5}{9}}\left(t^{3} - \tfrac{41}{20}\,t\right)
\]

### Explicit 1D values

| \(t\) | \(\varphi_{0}\) | \(\varphi_{1}\) | \(\varphi_{2}\) | \(\varphi_{3}\) |
|-------|-----------------|-----------------|-----------------|-----------------|
| \(-\tfrac{3}{2}\) | 0.5 | \(-\tfrac{3}{2\sqrt{5}}\) | 0.5 | \(-\tfrac{1}{2\sqrt{5}}\) |
| \(-\tfrac{1}{2}\) | 0.5 | \(-\tfrac{1}{2\sqrt{5}}\) | \(-0.5\) | \(\tfrac{3}{2\sqrt{5}}\) |
| \(\tfrac{1}{2}\) | 0.5 | \(\tfrac{1}{2\sqrt{5}}\) | \(-0.5\) | \(-\tfrac{3}{2\sqrt{5}}\) |
| \(\tfrac{3}{2}\) | 0.5 | \(\tfrac{3}{2\sqrt{5}}\) | 0.5 | \(\tfrac{1}{2\sqrt{5}}\) |

**Critical note:** \(\varphi_{3}\) is **not** proportional to raw \(t^{3}\); the projection onto \(\varphi_{1}\) is nonzero because \(\sum t^{4} = \tfrac{41}{4}\).

---

## 4. Two-dimensional tensor-product basis (16 modes)

\[
\Psi_{pq}(i,j) = \varphi_{p}(x_{i})\,\varphi_{q}(y_{j}),
\qquad p,q \in \{0,1,2,3\}
\]

Orthonormality follows from separability:

\[
\langle \Psi_{pq}, \Psi_{rs}\rangle
= \underbrace{\langle \varphi_{p}, \varphi_{r}\rangle}_{\delta_{pr}}
  \underbrace{\langle \varphi_{q}, \varphi_{s}\rangle}_{\delta_{qs}}
= \delta_{pr}\,\delta_{qs}
\]

The family \(\{\Psi_{pq}\}\) is a **complete** orthonormal basis for \(\mathbb{R}^{16}\).

---

## 5. Coefficients and inverse reconstruction

Field \(f\) on the grid (values \(f_{ij}\) at `(i,j)`).

**Forward (analysis):**

\[
c_{pq} = \langle f, \Psi_{pq}\rangle
= \sum_{i,j} f_{ij}\,\varphi_{p}(x_{i})\,\varphi_{q}(y_{j})
\]

**Inverse (synthesis):**

\[
f_{ij} = \sum_{p=0}^{3}\sum_{q=0}^{3} c_{pq}\,\varphi_{p}(x_{i})\,\varphi_{q}(y_{j})
\]

---

## 6. Parseval identity

\[
\|f\|^{2} = \sum_{p=0}^{3}\sum_{q=0}^{3} c_{pq}^{2}
\]

Equivalently: total cell-sum-of-squares equals sum of squared moment coefficients.

---

## 7. Centering and scaling conventions

### Raw grid values

Magic-square entries are integers \(1,\ldots,16\) in row-major order. No per-field z-scoring is applied in the primary convention.

### Mean / DC mode

\[
\mu = \frac{1}{16}\sum_{i,j} f_{ij}
\]

Because \(\Psi_{00} = \varphi_{0}^{2} \equiv \tfrac{1}{4}\) under sum-weight:

\[
c_{00} = \langle f, \Psi_{00}\rangle_{\Sigma} = \tfrac{1}{4}\sum_{i,j} f_{ij} = 4\mu
\qquad
\bigl(\tilde{c}_{00} = \mu \text{ under mean-weight}\bigr)
\]

**Centered field:**

\[
\tilde{f}_{ij} = f_{ij} - \mu
\]

All non-DC coefficients of \(\tilde{f}\) equal those of \(f\); only \(c_{00}\) changes (\(c_{00}(\tilde{f}) = 0\)).

### Optional display scaling

For UI heatmaps only (not for energy ratios): divide coefficients or reconstructed components by \(\max_{p,q}|c_{pq}|\) or a fixed scale. **Energy metrics always use unscaled coefficients.**

---

## 8. Degree / order grouping

**Total degree:** \(\deg(p,q) = p + q\).

| Degree | Count | Modes \((p,q)\) |
|--------|-------|-----------------|
| 0 | 1 | (0,0) |
| 1 | 2 | (0,1), (1,0) |
| 2 | 3 | (0,2), (1,1), (2,0) |
| 3 | 4 | (0,3), (1,2), (2,1), (3,0) |
| 4 | 3 | (1,3), (2,2), (3,1) |
| 5 | 2 | (2,3), (3,2) |
| 6 | 1 | (3,3) |

**Complete basis order** (documented default): sort by `(p+q, max(p,q), p, q)` — degree-first, then tie-break.

Index list:

```
 0:(0,0)  1:(0,1)  2:(1,0)  3:(1,1)  4:(0,2)  5:(2,0)
 6:(1,2)  7:(2,1)  8:(0,3)  9:(3,0) 10:(2,2) 11:(1,3)
12:(3,1) 13:(2,3) 14:(3,2) 15:(3,3)
```

---

## 9. Selected ordering: “higher moments”

**Definition (primary):** all modes with **total degree \(\ge 2\)** — 13 modes:

\[
\mathcal{H} = \{(p,q) : p+q \ge 2\}
\]

Ordered by the same `(p+q, max(p,q), p, q)` key (indices 3–15 in the complete list above).

**Excluded from \(\mathcal{H}\):** DC (0,0) and affine terms (0,1), (1,0).

**Contrast with complete basis:** all 16 modes. The label “higher moments” refers to the **selected subset** \(\mathcal{H}\), not the full tensor-product expansion.

**Optional affine block:** \(\mathcal{A} = \{(p,q) : p+q \le 1\}\) — **3 modes**: \((0,0)\), \((0,1)\), \((1,0)\) (DC plus the two linear directions; bilinear \((1,1)\) has degree 2 and is excluded).

---

## 10. Retained / residual energy (unambiguous denominators)

Let \(S \subseteq \{(p,q)\}\) be a retained mode set (e.g. \(S = \mathcal{H}\)).

Define energies:

| Symbol | Formula | Meaning |
|--------|---------|---------|
| \(E_{\text{total}}\) | \(\sum_{p,q} c_{pq}^{2}\) | Total \(\|f\|^{2}\) |
| \(E_{\text{dc}}\) | \(c_{00}^{2}\) | Constant-mode energy |
| \(E_{\text{nonconst}}\) | \(E_{\text{total}} - E_{\text{dc}}\) | All non-DC energy |
| \(E_{\text{retained}}(S)\) | \(\sum_{(p,q)\in S} c_{pq}^{2}\) | Energy in selected modes |
| \(E_{\text{residual}}(S)\) | \(E_{\text{total}} - E_{\text{retained}}(S)\) | Energy outside \(S\) |

**Partition identity (exact):**

\[
E_{\text{retained}}(S) + E_{\text{residual}}(S) = E_{\text{total}}
\]

### Fraction conventions (always state denominator)

| Metric | Numerator | Denominator | Use when |
|--------|-----------|-------------|----------|
| `retained_frac_total` | \(E_{\text{retained}}(S)\) | \(E_{\text{total}}\) | Overall share including DC |
| `retained_frac_nonconst` | \(E_{\text{retained}}(S) - \mathbf{1}_{(0,0)\in S}\,c_{00}^{2}\) | \(E_{\text{nonconst}}\) | Shape content excluding mean |
| `residual_frac_total` | \(E_{\text{residual}}(S)\) | \(E_{\text{total}}\) | Complement of retained vs total |
| `residual_frac_nonconst` | \(E_{\text{residual}}(S) - \mathbf{1}_{(0,0)\notin S}\,c_{00}^{2}\) | \(E_{\text{nonconst}}\) | Non-DC complement |

### Constant-field edge case

If \(f_{ij} \equiv c\): \(c_{00} = 4c\), all other \(c_{pq} = 0\), hence \(E_{\text{nonconst}} = 0\).

**Convention:** any fraction with denominator \(E_{\text{nonconst}}\) is defined as **`0`** when \(|E_{\text{nonconst}}| < \varepsilon\) (not NaN). Numerator is also 0 for constant fields, so this is consistent.

For \(S = \mathcal{H}\) on a normal magic square, degree-1 modes vanish numerically; thus \(E_{\mathcal{H}} = E_{\text{nonconst}}\) (verified: 340 for the Dürer square).

---

## 11. Numerical tolerance and browser feasibility

### Recommended tolerances

| Check | Threshold | Notes |
|-------|-----------|-------|
| Orthogonality off-diagonal | `< 1e-12` | Expect ~1e-16 in float64 |
| Parseval relative error | `< 1e-12` | \(\| \sum c^{2} - \|f\|^{2} \| / \max(1,\|f\|^{2})\) |
| Reconstruction max abs err | `< 1e-10` | \(\max_{ij}|f_{ij} - \hat{f}_{ij}|\) |
| Treat coefficient as zero | `< 1e-9` | For magic-square symmetry checks |
| Constant-field denominator | \(|E_{\text{nonconst}}| < 1e-15\) | Use safe ratio = 0 |

### Zero-dependency JavaScript

Fully feasible:

- Precompute `PHI[p][node]` (4×4 table) and optionally all 16×16 mode vectors.
- Coefficients: 16 dot products × 880 squares ≈ 14k multiply-adds — trivial.
- No linear algebra library required.
- Use `Float64Array` for grids; store `Math.sqrt(5)`, `Math.sqrt(5/9)`, `41/20` as constants.
- **Do not** use the naive \(\varphi_{3} = t^{3}/\|t^{3}\|\); must use Gram–Schmidt formula above.

See `S1_basis.js` for a reference implementation and `S1_verify_basis.py` for independent checks.

---

## 12. Magic-square structural note (sanity check)

For the classic magic square `[16,3,2,13, 5,10,11,8, 9,6,7,12, 4,15,14,1]`:

- \(c_{00} = 34\) (magic constant)
- \(c_{01}, c_{10} \approx 0\) (row/column balance kills linear modes)
- Nontrivial higher-mode coefficients at (1,2), (2,1), (2,3), (3,2)
- Complement square \(17 - f\) flips sign on odd-degree modes; even-degree modes unchanged

---

*End of derivation — 1215-M2-S1*
