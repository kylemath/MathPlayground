# Task Brief — 1215-M2

**From:** 1215-C
**To:** 1215-M2
**Date:** 2026-07-09

---

## Task

Define and independently verify centered coordinates, a complete orthogonal spatial basis on a 4×4 grid, moment coefficients, normalization, degree/order grouping, retained/residual energy metrics, and deterministic control ensembles.

## Deliverables

1. `manager_M2_report.md` synthesizing reviewed child findings.
2. Mathematical derivations, numerical verification scripts, and proposed formulas in this manager folder.
3. A proposed draft for the coordinator's `moments.md`.

## Acceptance Criteria

- [ ] Spawn 2–4 sub-subagents asynchronously and require each to use the exact persona and report template.
- [ ] Give explicit coordinates, weighted inner product, orthonormal basis construction, coefficient definition, Parseval identity, and normalization.
- [ ] Distinguish complete tensor-product modes from any selected “higher moments”; document ordering and residual-energy cutoffs.
- [ ] Define reproducible random permutations and 1/2/3 pair-swap perturbations, including whether swaps are sequential, distinct, and allowed to undo.
- [ ] Provide runnable numerical checks for orthogonality, completeness, Parseval, and expected low-mode magic constraints.
- [ ] Flag statistical design choices: seeds, sample sizes, aggregation, uncertainty, and paired versus independent controls.
- [ ] Do not edit `/Users/kylemathewson/MagicSK/MagicMomentExplorer`.

## Output Location

All files go in: `/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M2`

Report file: `manager_M2_report.md`

## Context

Definitions must be implementable in zero-dependency browser JavaScript and independently reproducible in a verification script.

## Dependencies

None initially; later reconcile with M1's canonical data conventions.
