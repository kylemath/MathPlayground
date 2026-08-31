# Task Brief — 1215-M3

**From:** 1215-C
**To:** 1215-M3
**Date:** 2026-07-09

---

## Task

Design a browser-feasible data schema and recommendations for a simple, modern, zero-dependency web application with separate HTML, CSS, and JavaScript, including filtering, sorting, summaries, selected-square diagram, moment-energy visualization, accessibility, and smoke testing.

## Deliverables

1. `manager_M3_report.md` synthesizing reviewed child findings.
2. Independent static prototypes, schema examples, size/performance tests, and accessibility notes inside this manager folder.
3. A proposed draft for the coordinator's `web_recommendations.md`.

## Acceptance Criteria

- [ ] Spawn 2–4 sub-subagents asynchronously and require each to use the exact persona and report template.
- [ ] Propose a compact, versioned browser data schema that supports 880 records, controls, classifications, and moment summaries.
- [ ] Specify UI states and interactions for filtering, stable sorting, selected-square inspection, and comparison views.
- [ ] Describe an accessible interactive 4×4 diagram and a dependency-free energy visualization.
- [ ] Address responsiveness, keyboard access, semantic HTML, contrast, reduced motion, empty/error/loading states, and local-file versus HTTP serving.
- [ ] Provide at least one independent static prototype or automated feasibility/smoke-test artifact without touching the main application folder.
- [ ] Do not edit `/Users/kylemathewson/MagicSK/MagicMomentExplorer`.

## Output Location

All files go in: `/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M3`

Report file: `manager_M3_report.md`

## Context

Initial work should use an explicitly provisional schema and later identify integration requirements for M1/M2 outputs.

## Dependencies

Initial recommendations are independent; final schema needs M1 classification fields and M2 moment definitions.
