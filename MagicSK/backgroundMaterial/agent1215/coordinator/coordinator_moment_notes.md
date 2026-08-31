# Coordinator Independent Moment Notes

## Recommended complete basis

Use one-dimensional coordinates `x = (-3,-1,1,3)` and the discrete inner product

`<f,g>_1 = (1/4) Σ_i f(x_i)g(x_i)`.

Orthogonalizing `1,x,x²,x³` gives the following orthonormal value vectors:

- `p0 = (1,1,1,1)`
- `p1 = (-3,-1,1,3)/√5`
- `p2 = (1,-1,-1,1)`
- `p3 = (-1,3,-3,1)/√5`

The centered square is `z_rc = value_rc - 8.5`. The 16 tensor modes are
`φ_ab(r,c) = p_a(c)p_b(r)`, `a,b ∈ {0,1,2,3}`, under
`<f,g> = (1/16) Σ_rc f_rc g_rc`.

Define coefficients and energy by

- `c_ab = (1/16) Σ_rc z_rc φ_ab(r,c)`
- `E_ab = c_ab²`
- `E_total = (1/16) Σ_rc z_rc² = Σ_ab E_ab` (Parseval)
- `share_ab = E_ab/E_total`

For any permutation of 1–16, `E_total = 21.25 = 85/4`. Thus controls and magic squares have identical total energy; the analysis is about redistribution among modes.

## Mode collection and “remaining energy”

The full 16-mode basis must be preserved even if the UI shows a selected collection. A defensible default ordering is total polynomial degree `d=a+b`, with stable tie-break `(d,b,a)` or a documented equivalent.

For cutoff `D`, define:

- retained share: `R_D = Σ_{a+b≤D} E_ab / E_total`
- higher-mode remaining share: `H_D = Σ_{a+b>D} E_ab / E_total = 1-R_D`

Always publish the exact included mode IDs with any named collection. “Higher moments” without the cutoff and tie policy is not reproducible. Since the constant coefficient is zero after centering and magic row/column sums force all nonconstant axis modes (`a=0 xor b=0`) to zero, a second useful display groups only the nine interaction modes with `a,b>0`; it must not replace the complete-basis definition.

## Independent numerical result

`coordinator_moment_audit.py` and `coordinator_moment_audit.json` checked all 880 local squares using only the Python standard library:

- maximum 1D Gram error: `1.39e-17`
- maximum Parseval error: `1.42e-14`
- maximum magic axis-mode magnitude: `5.98e-16`
- total energy for every square: exactly `21.25` at reported precision

The implementation should treat values below approximately `1e-12` as numerical zero while retaining full double precision in generated data.

## Control design recommendation

- Use a named, cross-language reproducible PRNG, not host-language `random()` semantics. PCG32 or xoshiro with published test vectors is suitable; JavaScript integer behavior must be explicitly implemented.
- Random-permutation controls: generate independent Fisher–Yates permutations of 1–16 from a fixed master seed.
- Swap controls: for each source square and replicate, start from the unperturbed square and apply exactly `k=1,2,3` sequential swaps. Each swap selects two distinct positions uniformly. Prefer disjoint transpositions within a replicate so “k swaps” changes exactly `2k` cells and cannot undo an earlier swap; if shared positions or undoing are allowed, state that and label the condition “k swap operations” rather than “k swapped pairs.”
- Use matched seeds/replicate indices across `k` where feasible, but regenerate each `k` condition from the original square.
- Store seed, PRNG/version, replicate count, swap policy, and aggregation rules. Summaries should include count, mean, standard deviation, median, and quantiles (at least 5%, 25%, 75%, 95%). For each source square, retain the same summary fields or a compact subset needed by the UI.
- Do not mix the 880 D4 representatives with all 7,040 orientations unless orientation weighting is an explicit experimental factor. Polynomial modes are coordinate-frame dependent; either analyze the fixed canonical orientation or average over all eight D4 images and say which.
