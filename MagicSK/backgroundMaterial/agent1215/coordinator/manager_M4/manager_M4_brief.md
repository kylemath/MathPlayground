# Task Brief — 1215-M4

**From:** 1215-C
**To:** 1215-M4
**Date:** 2026-07-09

---

## Task

Perform an initial independent verification design, then audit and integrate M1–M3 findings when their reports appear. Check provenance, formulas, exact counts, reproducibility, performance, browser feasibility, and cross-stream consistency.

## Deliverables

1. `manager_M4_report.md` synthesizing reviewed child audits.
2. Independent verification scripts/checklists/results within this manager folder.
3. A proposed draft for the coordinator's `verification.md`.

## Acceptance Criteria

- [ ] Spawn 2–4 sub-subagents asynchronously and require each to use the exact persona and report template.
- [ ] Independently verify the central 880/7,040, D4-orbit, basis, Parseval, control-generation, schema, accessibility, and browser-feasibility claims.
- [ ] Read and cite M1–M3 reports/artifacts before finalizing; distinguish reproduced results from inspection-only conclusions.
- [ ] Run relevant scripts with fixed commands and capture observed outputs; use a virtual environment for any pip installs.
- [ ] Identify and resolve or explicitly report cross-stream conflicts, missing fields, ambiguous formulas, performance risks, and unsupported exact counts.
- [ ] Do not edit `/Users/kylemathewson/MagicSK/MagicMomentExplorer`.

## Output Location

All files go in: `/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M4`

Report file: `manager_M4_report.md`

## Context

Start with independent test plans and small verification prototypes while M1–M3 run. Poll their report paths at reasonable intervals or inspect once available, then complete integration.

## Dependencies

Final audit depends on:
- `/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M1/manager_M1_report.md`
- `/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M2/manager_M2_report.md`
- `/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M3/manager_M3_report.md`
