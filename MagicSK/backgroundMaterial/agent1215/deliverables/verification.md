# Verification and Reproducibility Audit

## Boundary

All coordinator and manager artifacts were written under `backgroundMaterial/agent1215`. The main `MagicMomentExplorer` application was treated as read-only. Verification outputs and rebuilt analysis files were directed into the orchestration tree.

## Evidence levels

The report uses three labels:

- **Reproduced:** a command was run and its output inspected.
- **Inspected:** code/data were reviewed but the full computation was not rerun.
- **Literature:** claim supported by a cited external source.

This distinction is important: validating a supplied 880-row CSV does not independently enumerate all possible squares.

## Dataset audit — reproduced

Command:

```text
python3 backgroundMaterial/agent1215/coordinator/coordinator_dataset_audit.py \
  MagicMomentExplorer/data/magic_squares_880.csv \
  --output backgroundMaterial/agent1215/coordinator/coordinator_dataset_audit.json
```

Observed:

- 880 records, IDs 1–880
- all normal and magic
- 880 literal grids and 880 D4 canonical forms
- every source row lexicographically canonical
- orbit-size histogram `{8: 880}`
- expanded oriented union `7,040`
- all complement targets present and all declared `complement_id` values consistent
- Dudeney distribution `48,48,48,96,96,304,56,56,56,56,8,8`

The audit is Python standard library only and completed in under one second on the test host.

## Classification audit — reproduced

M1 supplied `coordinator/manager_M1/sub_S3/classify_counts.py`; M4 executed its CSV audit independently.

Observed on D4 canonical classes:

- magic 880
- pandiagonal 48
- semi-pandiagonal 48
- associative 48
- most-perfect 48
- compact non-toroidal 2×2 48
- self-complementary up to D4 352
- complement action: 352 singleton classes and 264 paired orbits

The predicate implementations are the authority for these labels. Historical synonyms should not be substituted without carrying the tested line/block definitions.

## Moment audit — reproduced

Coordinator command:

```text
python3 backgroundMaterial/agent1215/coordinator/coordinator_moment_audit.py \
  MagicMomentExplorer/data/magic_squares_880.csv \
  --output backgroundMaterial/agent1215/coordinator/coordinator_moment_audit.json
```

Mean-normalized independent result:

- maximum 1D Gram error `1.39e-17`
- maximum Parseval error `1.42e-14`
- maximum magic axial-mode magnitude `5.98e-16`
- centered mean energy exactly `21.25` for every permutation

M4 independently audited the sum-normalized application convention on 4,400 records:

- maximum 1D Gram error approximately `6.7e-16`
- 16 tensor modes complete
- zero Parseval failures
- zero coefficient mismatches at the stated tolerance
- reconstruction error below approximately `1e-14` on tested records
- `axialEnergy + interactionEnergy + C00² = 340` after centering, with `C00=0`
- all 880 magic records have zero axial energy at stored precision

The mean and sum conventions differ by scaling but yield the same normalized shares. The deliverable `moments.md` fixes the sum-normalized convention to prevent schema mismatch.

## Pipeline reproducibility — reproduced by M4

M4 reran the read-only application analysis into its own output folder:

```text
python3 MagicMomentExplorer/scripts/analyze.py \
  --input MagicMomentExplorer/data/magic_squares_880.csv \
  --output-dir backgroundMaterial/agent1215/coordinator/manager_M4/rebuilt_analysis \
  --random-count 880 \
  --seed 20260709
```

Observed:

- 4,400 records written
- rebuilt JSON and CSV byte-identical to the inspected checked-in artifacts at audit time
- JSON SHA-256 `95908addccce69f88299f410eb4e5def0c1b30b356b0fb5e727a7c48345148c9`
- CSV SHA-256 `09abd51a0cf18184c702ba7ab3c9712ab53d96bd942384720fb9068331d7d005`
- all 2,640 swap and 880 random cell arrays matched a deterministic replay
- all aggregate cohort summaries matched independent recomputation

This verifies that specific pipeline snapshot, seed, Python PRNG, call order, and swap implementation. It does not make a separately proposed Mulberry32 control generator equivalent.

## Control cohorts — reproduced current behavior

The audited pipeline has 880 records in each cohort:

- baseline magic
- one disjoint pair swap
- two disjoint pair swaps
- three disjoint pair swaps
- random permutation

For a `k`-swap record it samples `2k` distinct positions and pairs them, so exactly `2k` cells change and no swap can undo another within that record. All control grids remain permutations of 1–16. In the audited realization, none of the 3,520 controls remained magic.

Observed cohort means from M4:

- magic: axial energy `0`, line-defect energy `0`
- random: mean axial energy `136.454545`, mean line-defect energy `677.177273`
- swap-1: mean axial energy `32.821023`, mean line-defect energy `161.654545`
- swap-2: mean axial energy `63.568750`, mean line-defect energy `315.690909`
- swap-3: mean axial energy `84.637500`, mean line-defect energy `429.363636`

These are descriptive results for one deterministic realization per source, not uncertainty intervals. A publication-grade rerun should use repeated per-square controls as specified in `moments.md`.

## Web feasibility — reproduced/inspected

M3 produced two independent artifacts:

- a compact 880-record schema/payload prototype
- a zero-dependency static interaction prototype with a Node smoke runner

Measured compact payload:

- approximately 152,039 bytes uncompressed
- approximately 32,481 bytes gzip
- desktop Node parse/normalize/filter operations in low single-digit milliseconds

Recorded static prototype smoke result:

- coordinator rerun: 45 checks passed, 0 failed
- verified required files, semantic hooks, module exports, sample schema, and HTTP fetch

Limits:

- desktop Node timings are not low-end mobile browser benchmarks
- static hooks do not prove keyboard or screen-reader usability
- the sample visual prototype uses 20 records
- coefficient rounding and provisional class flags require integration changes described in `web_recommendations.md`

## Cross-stream conflicts reviewed

1. **Sum versus mean moment normalization:** both were mathematically valid but numerically incompatible. Resolved by selecting the sum-inner-product convention in `moments.md` and documenting the conversion.
2. **Horizontal/vertical mode index order:** fixed as first index = column/horizontal degree, second = row/vertical degree.
3. **“15 interaction modes”:** corrected. There are 15 non-DC modes, comprising six axial and nine interaction modes.
4. **Control PRNG:** existing Python `random.Random` outputs and proposed Mulberry32 outputs differ. Both may be reproducible, but one versioned protocol must be selected.
5. **Uniform bounded draws:** multiplying a 32-bit float and flooring has tiny modulo bias. Rejection-sampled bounded integers are recommended for an exact-uniform claim.
6. **Complement-pair count:** “440 pairs” was rejected. The reproduced D4-class action has 352 fixed classes plus 264 two-class orbits.
7. **From-scratch enumeration:** an early M1 attempt produced an empty result and was not accepted as evidence. The final count is supported by literature plus complete local snapshot/orbit validation unless a corrected generator is run.
8. **Schema rounding:** four-decimal coefficients are compact but may drift Parseval; use at least eight decimals or store energies independently with a tolerance policy.
9. **M2-S2 report formulas:** its displayed cubic formula was inconsistent with its verified script, and its claim that `M22=0` was only empirical was incorrect. The reviewed deliverable uses the verified cubic basis and notes that `M22` is forced by the row, column, and two principal-diagonal constraints.

## Recommended release gates

- Pin and hash source pages and generated CSV.
- Run dataset, D4, complement, and classification audits from a clean checkout.
- Run orthogonality, Parseval, reconstruction, and coefficient-order tests.
- Version the exact control PRNG and swap protocol; rerun twice and compare hashes.
- Validate every browser record, not only a sample.
- Generate JSON and embedded JavaScript from the same artifact and compare hashes.
- Run Node/static smoke tests.
- Serve over HTTP and manually test current Safari, Firefox, and Chromium.
- Complete keyboard-only, 200% zoom, reduced-motion, and VoiceOver checks.

## Remaining risks

- Source redistribution licensing remains unclear.
- Historical “semi-pandiagonal” terminology is not completely standardized.
- The current one-control-per-square cohorts do not quantify within-square uncertainty.
- Browser accessibility has a strong prototype and test plan but not a recorded assistive-technology certification.
