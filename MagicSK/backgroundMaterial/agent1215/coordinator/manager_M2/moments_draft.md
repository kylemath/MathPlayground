# Draft `moments.md` — 4×4 Spatial Moments and Deterministic Controls

**Proposed specification:** 1215-M2  
**Date:** 2026-07-09  
**Status:** Independently verified draft

---

## 1. Grid, coordinates, and indexing

For row `r` and column `c` in `{0,1,2,3}`, use row-major index
`k = 4r + c`. The centered spatial coordinates are

$$
x_c=c-\frac32,\qquad y_r=r-\frac32,
$$

so each axis is `{-3/2,-1/2,1/2,3/2}`. The moment label `M_pq` means
column/x degree `p` and row/y degree `q`.

For values $F_{rc}$, define

$$
\mu=\frac1{16}\sum_{r,c}F_{rc},\qquad G_{rc}=F_{rc}-\mu.
$$

For every permutation of `1..16`, $\mu=8.5$ and

$$
\frac1{16}\sum G_{rc}^2=\frac{16^2-1}{12}=\frac{255}{12}=21.25.
$$

## 2. Inner products and complete orthonormal basis

Use uniform mean-weight inner products:

$$
\langle u,v\rangle_1=\frac14\sum_{i=0}^{3}u_i v_i,\qquad
\langle A,B\rangle_2=\frac1{16}\sum_{r,c}A_{rc}B_{rc}.
$$

An exact 1D orthonormal polynomial basis, listed in node order, is

$$
\begin{aligned}
P_0&=[1,1,1,1],\\
P_1&=\frac1{\sqrt5}[-3,-1,1,3],\\
P_2&=[1,-1,-1,1],\\
P_3&=\frac1{\sqrt5}[-1,3,-3,1].
\end{aligned}
$$

As functions of $t\in\{-3/2,-1/2,1/2,3/2\}$:

$$
P_0(t)=1,\quad
P_1(t)=\frac{2t}{\sqrt5},\quad
P_2(t)=t^2-\frac54,\quad
P_3(t)=\frac{20t^3-41t}{6\sqrt5}.
$$

Define all 16 tensor-product modes

$$
\Psi_{pq}(r,c)=P_p(x_c)P_q(y_r),\qquad 0\le p,q\le3.
$$

They satisfy

$$
\langle\Psi_{pq},\Psi_{ab}\rangle_2=\delta_{pa}\delta_{qb}.
$$

There are 16 orthonormal vectors in the 16-dimensional space of real
4×4 fields, so this basis is complete.

### Equivalent sum-weight normalization

The child derivations also use $\sum$ rather than the mean as the inner
product. Their 1D basis is $\phi_p=P_p/2$, their 2D basis is
$\psi_{pq}=\Psi_{pq}/4$, and their coefficients and energies satisfy

$$
c^{(\mathrm{sum})}_{pq}=4c^{(\mathrm{mean})}_{pq},\qquad
E^{(\mathrm{sum})}=16E^{(\mathrm{mean})}.
$$

Normalized energy fractions are invariant. Production should use only the
mean-weight convention above, which makes the DC coefficient equal to the
arithmetic mean.

## 3. Coefficients, reconstruction, and Parseval

For either raw $F$ or centered $G$:

$$
c_{pq}=\langle F,\Psi_{pq}\rangle_2
=\frac1{16}\sum_{r,c}F_{rc}P_p(x_c)P_q(y_r).
$$

The inverse and Parseval identities are

$$
F_{rc}=\sum_{p=0}^{3}\sum_{q=0}^{3}c_{pq}\Psi_{pq}(r,c),
\qquad
\frac1{16}\sum_{r,c}F_{rc}^2=\sum_{p,q}c_{pq}^2.
$$

Here $c_{00}=\mu$. Centering changes only $c_{00}$; every nonconstant
coefficient is unchanged.

## 4. Degree grouping and documented selections

Total degree is $d=p+q$. The canonical complete ordering is total degree,
then increasing `p`:

```text
d0: (0,0)
d1: (0,1), (1,0)
d2: (0,2), (1,1), (2,0)
d3: (0,3), (1,2), (2,1), (3,0)
d4: (1,3), (2,2), (3,1)
d5: (2,3), (3,2)
d6: (3,3)
```

The complete basis is always these 16 modes. “Higher moments” is a selected
ordered subset, not another basis:

$$
\mathcal H=\{(p,q):p+q\ge2\},
$$

with the 13 modes inherited from the canonical order. For analyses focused
on row/column-balanced structure, also expose the explicitly named
interaction block

$$
\mathcal I=\{(p,q):p\ge1,\ q\ge1\},
$$

whose inherited order is
`(1,1),(1,2),(2,1),(1,3),(2,2),(3,1),(2,3),(3,2),(3,3)`.
Never label $\mathcal H$ or $\mathcal I$ as the complete expansion.

## 5. Energy and normalization metrics

For centered $G$, define

$$
E_{\mathrm{nc}}=\frac1{16}\sum G_{rc}^2
=\sum_{(p,q)\ne(0,0)}c_{pq}^2.
$$

For a retained set $S\subseteq\{(p,q):(p,q)\ne(0,0)\}$:

$$
E_{\mathrm{ret}}(S)=\sum_{(p,q)\in S}c_{pq}^2,\qquad
E_{\mathrm{res}}(S)=E_{\mathrm{nc}}-E_{\mathrm{ret}}(S).
$$

Report the fractions

$$
R_{\mathrm{ret}}=\frac{E_{\mathrm{ret}}}{E_{\mathrm{nc}}},\qquad
R_{\mathrm{res}}=\frac{E_{\mathrm{res}}}{E_{\mathrm{nc}}}=1-R_{\mathrm{ret}}.
$$

The denominator is always the centered/nonconstant energy. If
$E_{\mathrm{nc}}\le10^{-15}\max(1,\mu^2)$, both fractions are mathematically
undefined; return `null` with `defined:false` and display “N/A”, rather than
silently treating a constant field as having zero or full retained share.

Optional RMS standardization uses

$$
\sigma=\sqrt{E_{\mathrm{nc}}},\qquad Z_{rc}=G_{rc}/\sigma,\qquad
a_{pq}=c_{pq}/\sigma,
$$

so $\sum_{(p,q)\ne(0,0)}a_{pq}^2=1$. For normal 4×4 permutations,
$\sigma=\sqrt{85}/2$, a fixed scale.

## 6. Exact implications of magic constraints

Equal column sums force

$$
c_{10}=c_{20}=c_{30}=0,
$$

and equal row sums force

$$
c_{01}=c_{02}=c_{03}=0.
$$

Thus a centered row/column-balanced square has energy only in the nine mixed
modes $\mathcal I$.

For a full magic square, centered main- and anti-diagonal sums also vanish.
Orthonormality and parity $P_p(-t)=(-1)^pP_p(t)$ give

$$
c_{11}+c_{22}+c_{33}=0,\qquad
-c_{11}+c_{22}-c_{33}=0.
$$

Therefore

$$
c_{22}=0,\qquad c_{33}=-c_{11}.
$$

These are exact consequences of both diagonal constraints, not empirical
coincidences. Row and column constraints alone do not force $c_{22}=0$.

## 7. Deterministic control ensembles

### 7.1 PRNG and unbiased integer draws

Use a documented uint32 Mulberry32 stream for cross-language reproducibility.
All multiplication in JavaScript must use `Math.imul`, and all states/results
must be coerced with `>>> 0`. Obtain a raw uint32 output `x`.

For uniform `randBelow(n)`, do not use `floor(u*n)`. Let

```text
limit = 2^32 - (2^32 mod n)
draw x until x < limit
return x mod n
```

This rejection step removes finite-word modulo bias. Fisher–Yates then gives
an exact uniform permutation under the PRNG model: for `i=15..1`, draw
`j=randBelow(i+1)` and swap entries `i,j`. Shuffle the supplied base value
multiset, not a hard-coded `1..16` array.

Derive per-replicate streams with uint32 avalanche mixing:

```text
mix32(x):
  x ^= x >>> 16
  x = imul(x, 0x7feb352d)
  x ^= x >>> 15
  x = imul(x, 0x846ca68b)
  x ^= x >>> 16
  return x >>> 0

seed(base, squareId, replicate, tag) =
  mix32(base ^ imul(squareId, 0x9e3779b1)
             ^ imul(replicate, 0x85ebca77)
             ^ tag)
```

Use distinct fixed tags `0xa341316c` for random permutations and
`0xc8013ea4` for swaps. This domain separation makes the random-permutation
arm independent of the paired swap path at the pseudorandom-stream level.

### 7.2 Sequential one-, two-, and three-swap controls

Enumerate the 120 unordered position pairs lexicographically:
`(a,b)` with `0 <= a < b < 16`. For each `(squareId, replicate)`:

1. Use the swap-tagged stream to sample three distinct pair IDs without
   replacement, preferably by the first three steps of a Fisher–Yates shuffle
   of IDs `0..119`.
2. Different pair identities may share a cell.
3. Self-pairs/no-ops are absent by construction.
4. Repeating the same unordered pair is forbidden, so immediate direct undo
   is forbidden.
5. Apply the pairs sequentially to the original square. `SWAP1`, `SWAP2`,
   and `SWAP3` are the first one, two, and three states on the same path.
6. Do not reject indirect cancellations, endpoint collisions, or reduced
   Hamming distance. They are valid consequences of distinct sequential
   transpositions.

This is uniform over ordered length-$k$ sequences of distinct pair IDs, not
uniform over reachable endpoint grids.

### 7.3 Sample sizes and summaries

- Browser preview: `B=256` replicates per source square.
- Production/offline default: `B=4096`.
- Tail-sensitive sensitivity run: `B=10000` or larger.
- Record base seed, algorithm version, sample size, source-square ID, and
  control protocol in the output manifest.

For each source square and condition, report `n`, mean, sample standard
deviation, Monte Carlo standard error, and linearly interpolated
`q05/q25/q50/q75/q95` for each coefficient, degree energy, retained fraction,
and residual fraction. Under paired prefixes, also summarize within-replicate
differences `SWAP2-SWAP1` and `SWAP3-SWAP2`.

When combining source squares, first compute each square’s condition summary,
then average square summaries with equal source-square weight. Distinguish
Monte Carlo uncertainty conditional on a square from source-square
heterogeneity. For generalization across squares, use a deterministic
cluster bootstrap over source-square IDs or a square-level standard error;
never treat all control replicates across all squares as independent source
observations.

## 8. Browser implementation and tolerances

The basis requires only a 4×4 constant table and 16 dot products of length 16.
`Float64Array` and ordinary `Number` arithmetic are sufficient; no numerical
library is needed.

Recommended checks:

- basis Gram and relative Parseval error: `1e-12`;
- reconstruction max absolute error: `1e-10`;
- theoretical zero coefficient: scale-aware
  `abs(c) <= 1e-12 * max(1, sqrt(E_nc))`;
- UI display-zero threshold: `1e-9 * max(1, sqrt(E_nc))`;
- integer row/column/diagonal sums: exact integer comparison.

Keep full-precision coefficients internally and round only for display.

## 9. Independent observed verification

Run:

```bash
python3 verify_manager_spec.py
```

The captured `manager_verification_output.json` reports:

- 16 modes;
- 1D Gram max error `1.39e-17`;
- 2D Gram max error `2.22e-16`;
- reconstruction max error `1.78e-15`;
- Parseval absolute error `2.84e-14`;
- magic axial-mode max `1.11e-16`;
- both diagonal-relation errors `6.94e-17`;
- $|c_{22}|=0$ and $|c_{33}+c_{11}|=6.94e-17$;
- centered energy `21.249999999999996`, versus exact `21.25`.

All checks pass the stated tolerances.

---

*Draft prepared by Manager 1215-M2 — 2026-07-09*
