# Spatial Moments and Energy Specification

## Primary convention

Use row-major cells `a[r,c]`, with row `r` increasing top-to-bottom and column `c` left-to-right. Coordinates are

`t = (-3/2, -1/2, 1/2, 3/2)`.

Use the unweighted discrete one-dimensional inner product

`<f,g>₁ = Σᵢ f(tᵢ)g(tᵢ)`.

Gram–Schmidt orthonormalization of `1,t,t²,t³` gives:

- `φ₀ = (1,1,1,1)/2`
- `φ₁ = (-3,-1,1,3)/(2√5)`
- `φ₂ = (1,-1,-1,1)/2`
- `φ₃ = (-1,3,-3,1)/(2√5)`

Equivalently:

- `φ₀(t)=1/2`
- `φ₁(t)=t/√5`
- `φ₂(t)=(t²-5/4)/2`
- `φ₃(t)=√(5/9)(t³-(41/20)t)`

The cubic projection term is essential; raw `t³` is not orthogonal to `t`.

Define the tensor mode with horizontal degree `p` and vertical degree `q` by

`Ψ[p,q](r,c) = φₚ(t_c) φ_q(t_r)`.

This convention fixes the first index as column/horizontal degree and the second as row/vertical degree. The 16 modes for `p,q∈{0,1,2,3}` are a complete orthonormal basis of all real 4×4 fields.

## Centering, coefficients, and Parseval

Center values once:

`h[r,c] = a[r,c] - 8.5`.

Define:

- coefficient: `C[p,q] = Σᵣ,c h[r,c] Ψ[p,q](r,c)`
- mode energy: `E[p,q] = C[p,q]²`
- centered total energy: `E_total = Σᵣ,c h[r,c]² = Σₚ,q E[p,q]`

Every permutation of 1–16 has fixed `E_total = 340`. Centering makes `C[0,0]=0`.

A mean-inner-product convention is mathematically equivalent if every basis vector and coefficient is scaled consistently; it gives total energy `340/16 = 21.25`. Do not mix coefficients from the two conventions. Store the convention in schema metadata. The sum convention above matches the independently audited analysis pipeline.

Independent results:

- 1D Gram error at most approximately `6.7e-16`
- Parseval and reconstruction passed on 4,400 audited records
- all 880 magic squares have the six nonconstant axial coefficients numerically zero
- use `1e-12` as a practical zero tolerance before output rounding

## Why magic squares remove axial energy

Axial modes have exactly one zero index:

`(1,0),(2,0),(3,0),(0,1),(0,2),(0,3)`.

Each centered row and column of a magic square sums to zero because its raw sum is 34. Consequently every nonconstant axial coefficient vanishes. The two principal-diagonal constraints additionally force `C[2,2]=0`: the sign mask of `Ψ[2,2]`, up to scale, is a linear combination of the four row, four column, main-diagonal, and anti-diagonal incidence vectors. Thus all centered energy of an exact magic square lies in at most eight nonzero interaction modes with `p>0`, `q>0`, excluding `(2,2)`.

This property is useful for comparing perturbed and random squares: energy transferred into axial modes measures broken row/column balance.

## Documented energy collections

Keep all 16 coefficients internally. Do not call all 15 non-DC modes “interaction modes.”

Recommended derived groups:

- `axialEnergy = Σ E[p,q]` for exactly one of `p,q` equal to zero
- `interactionEnergy = Σ E[p,q]` for `p,q>0`
- `degreeEnergy[d] = Σ E[p,q]` for `p,q>0` and `p+q=d`, `d=2..6`
- `lowInteractionEnergy = degreeEnergy[2] + degreeEnergy[3]`
- `highInteractionEnergy = degreeEnergy[4] + degreeEnergy[5] + degreeEnergy[6]`
- `spectralCentroid = Σ d·degreeEnergy[d] / interactionEnergy`, null if interaction energy is zero

Two cumulative “energy remaining” families should be exposed with distinct names:

1. **Complete-basis higher-degree share**

   `H_all(D) = Σ_{p+q>D} E[p,q] / 340`.

   This measures all energy above total polynomial degree `D`, including any high-degree axial imbalance in controls.

2. **Higher interaction share**

   `H_interaction(D) = Σ_{p,q>0; p+q>D} E[p,q] / 340`.

   This measures high spatial interaction relative to the fixed total permutation energy. It decreases when swaps move energy into axial modes.

An optional conditional shape statistic,

`H_interaction_conditional(D) = Σ_{p,q>0; p+q>D} E[p,q] / interactionEnergy`,

describes the spectrum only after conditioning on remaining interaction energy. It must not replace the fixed-denominator metric when comparing magic and nonmagic controls.

Useful cutoffs are `D=2,3,4,5`; `D=6` is identically zero. Publish the included mode IDs and denominator alongside every chart.

## Orientation policy

Polynomial modes are coordinate-frame dependent. Analyze the stored canonical orientation for the primary 880-record view. If rotation/reflection invariance is desired, add a separate explicitly named statistic that averages each energy metric over all eight D4 images. Do not mix canonical-orientation and orbit-averaged values in one distribution.

## Control ensembles

### Random permutations

Generate independent unbiased Fisher–Yates permutations of `1..16`. If the PRNG exposes 32-bit integers, use rejection sampling for bounded integers; `floor(u*n)` has a tiny modulo bias whenever `n` does not divide `2³²`.

### Pair-swap perturbations

For condition `k∈{1,2,3}`:

1. Start from the original canonical square.
2. Select `2k` distinct cell indices uniformly without replacement.
3. Pair consecutive sampled indices and swap within each pair.

This gives `k` disjoint pair swaps, changes exactly `2k` cells, and cannot undo an earlier swap. It matches the plain-language interpretation of “1, 2, or 3 pair swaps.” If a with-replacement transposition random walk is studied, label it “k swap operations” and report its repeat/undo policy and effective Hamming distance separately.

Generate each `k` condition from the original square. For paired comparisons, derive deterministic seeds from `(masterSeed, squareId, replicateId, condition)` rather than relying on global call order.

### Sample size and summaries

For a publication-grade comparison, use at least 200 replicates per source square per condition, or justify a convergence-based alternative. One random/swap realization per source square gives a useful 880-member illustrative cohort but cannot estimate within-square control uncertainty.

Store:

- PRNG name/version and bounded-integer algorithm
- master seed and deterministic seed-derivation rule
- square IDs, replicate count, orientation policy
- random-shuffle and swap-pair algorithms
- whether conditions are paired
- mean, population standard deviation, median, and 5/25/75/95 percentiles

Summarize both:

- across all generated grids by condition, and
- per source square across replicates, so the selected-square UI has a matched control distribution.

## Existing verified pipeline versus recommended next run

The independently audited existing analysis uses Python `random.Random(20260709)`, one disjoint-pair perturbation for each `k` per source, and one random permutation per source, producing 4,400 records. It reproduced exactly when rerun and is valid as a deterministic illustrative cohort.

A separate M2 prototype uses Mulberry32, repeated simulations, and configurable transposition walks. It is useful design work but does not reproduce the existing control cells. The final application must choose one protocol and version it; it must not imply the two seeded outputs are interchangeable.

## Browser implementation

- Precompute basis values as 64-bit numbers and mode IDs such as `M10`.
- Store coefficients at enough precision for stable charts; eight decimal places passed the existing audit, while four decimals may visibly drift Parseval.
- Recompute energy as squared coefficients in JavaScript if desired.
- Ship aggregate controls in the primary payload and lazy-load individual replicates only if the UI needs them.
- Include `basisId`, coordinate order, normalization, coefficient orientation, mode order, energy denominator, PRNG/protocol IDs, and pipeline version in metadata.
