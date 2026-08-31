# Independent Verification Plan — 1215-M4

**Date:** 2026-07-09  
**Phase:** Independent verification before M1–M3 integration

## Verification Matrix

1. **Dataset and D4 census**
   - Validate all 880 CSV rows are permutations of 1–16 with ten line sums equal to 34.
   - Canonicalize each row over the eight geometric D4 transforms.
   - Check 880 distinct canonical classes, each with orbit size eight.
   - Expand every canonical class and check the union has exactly 7,040 oriented squares.
   - Distinguish source-audit reproduction from a from-scratch enumeration.
   - Recompute structural predicates and report exact counts only with executable evidence.

2. **Formula and numerical checks**
   - Construct the four one-dimensional basis functions and evaluate the Gram matrix.
   - Form all 16 tensor-product modes and check rank/completeness.
   - Check reconstruction and Parseval on source squares and deterministic controls.
   - Reconcile sum-inner-product versus mean-inner-product conventions before schema integration.
   - Verify the six nonconstant axial coefficients vanish for every valid magic square.

3. **Control design**
   - Record PRNG algorithm, seed, sample count, per-square versus global sampling, replacement rules, whether swaps can undo, and paired-prefix versus independently resampled k-swap cohorts.
   - Check deterministic reruns and aggregation denominators.
   - Treat a single control per source as an illustrative cohort, not uncertainty estimation.

4. **Schema/browser/accessibility**
   - Map M1 identifiers, provenance, classifications, orbit/complement fields and M2 coefficient/energy/control metadata into M3's versioned schema.
   - Validate all records, not only the first record.
   - Measure uncompressed payload size and recommend compression and/or a magic-only initial payload.
   - Check keyboard activation, focus visibility, semantic tables, canvas text alternatives, live-region behavior, contrast, reduced motion, responsive overflow, and file:// fallback.

## Preliminary Executed Checks

### CSV/classification audit

Command:

```text
python3 "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M1/sub_S3/classify_counts.py" --csv "/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv" --output "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/independent_csv_audit.json"
```

Observed: exit 0; 880 records; 880 D4 canonical forms; orbit-size distribution `{8: 880}`; 880 valid magic records; exact structural counts included in `independent_csv_audit.json`. The script's `oriented_count: 880` is not an expansion result in CSV-audit mode: its implementation counts the supplied rows only. The orbit evidence implies 7,040 only after checking that expanded classes are disjoint; that check remains explicit in the independent S1 audit.

### Deterministic analysis rebuild

Command:

```text
python3 "/Users/kylemathewson/MagicSK/MagicMomentExplorer/scripts/analyze.py" --input "/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv" --output-dir "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/rebuilt_analysis" --random-count 880 --seed 20260709
```

Observed: exit 0; wrote 4,400 records.

Comparison command:

```text
shasum -a 256 "/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.json" "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/rebuilt_analysis/analysis.json" "/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.csv" "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/rebuilt_analysis/analysis.csv" && cmp -s "/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.json" "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/rebuilt_analysis/analysis.json" && echo "analysis.json byte-identical" && cmp -s "/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.csv" "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4/rebuilt_analysis/analysis.csv" && echo "analysis.csv byte-identical"
```

Observed: exit 0. JSON SHA-256 `95908addccce69f88299f410eb4e5def0c1b30b356b0fb5e727a7c48345148c9`; CSV SHA-256 `09abd51a0cf18184c702ba7ab3c9712ab53d96bd942384720fb9068331d7d005`; both files byte-identical to the checked-in files. Sizes were 4,391,099 bytes JSON and 823,879 bytes CSV.

## Preliminary Risks

- A CSV audit is not an independent from-scratch census; provenance and enumeration evidence must be reported separately.
- The current app analysis uses sum-orthonormal basis vectors and unscaled coefficient sums; one M2 prototype uses mean-orthonormal vectors and coefficients divided by 16. Both can satisfy Parseval, but their coefficient and energy fields are numerically incompatible unless a convention is fixed and versioned.
- The current application directory references `styles.css`, `moments.js`, `app.js`, and `data/analysis-data.js`, but those files were not present in the initial six-file inventory. Browser readiness must not be inferred from `index.html` alone.
- The checked-in 4.39 MB JSON is feasible under HTTP but expensive to parse synchronously on lower-end devices and unavailable to the current `index.html` as written because the referenced generated JavaScript payload is absent.
