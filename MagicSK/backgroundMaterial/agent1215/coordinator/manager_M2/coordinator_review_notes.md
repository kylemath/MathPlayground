# Coordinator Review Notes for M2

Please resolve these before finalizing `manager_M2_report.md`:

1. Fix normalization language across children. With centered values and mean inner products, total energy is `21.25`. With raw values, total mean-square is `93.5`, including DC energy `72.25`. `S3_report.md` uses both conventions; choose and version one primary convention and give an exact conversion.
2. `floor(u*n)` from a 32-bit PRNG is not exactly uniform unless `n` divides `2^32`. The resulting bias is tiny for `n≤120`, but the report calls Fisher–Yates “exact uniform.” Either implement rejection-sampled bounded integers in both Python and JavaScript, or accurately label the negligible modulo bias.
3. Select and justify the default swap policy. “Pair swaps” commonly suggests distinct/disjoint pairs; a with-replacement random walk can undo itself. If retained, label it `k swap operations`, expose effective Hamming-distance behavior, and keep a strict disjoint-pair sensitivity condition.
4. A degree cutoff of 1 leaves all centered magic-square energy in the residual because constant and axial first-order modes vanish. It is not informative as the sole higher-moment metric. Define a documented cutoff collection (or several cumulative cutoffs) over the complete 16-mode basis.
5. Reconcile 1D coordinate scaling (`±1.5,±0.5` versus `±3,±1`) and sum versus mean orthonormality. Equivalent bases may differ only by construction inputs, but coefficients/energies must have a single published convention.
6. Cite the coordinator's independent check where useful: `../coordinator_moment_audit.py`, `../coordinator_moment_audit.json`, and `../coordinator_moment_notes.md`.
7. Correct two substantive errors in `sub_S2/S2_report.md`:
   - Its displayed cubic formula `(4t³ − 3.75t)/√365` (and claimed equivalence to raw `4t³/√365`) does not match the verified Gram–Schmidt basis. Use `√(5/9)(t³−41t/20)` or the explicit vector.
   - `M22=0` is not merely an unexplained empirical invariant. Its sign pattern is in the span of the four row, four column, and two principal-diagonal constraint vectors. With the report's scaling, the unscaled `M22` sign mask equals `2(main diagonal)+2(anti-diagonal)−(1/2)Σ(rows)−(1/2)Σ(columns)`, so centered equal row/column/diagonal sums force `M22=0`. The offered semi-magic counterexample fails the diagonal constraints and therefore does not show insufficiency.
