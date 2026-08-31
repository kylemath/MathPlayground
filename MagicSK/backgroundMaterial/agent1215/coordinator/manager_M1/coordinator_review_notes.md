# Coordinator Review Notes for M1

Please resolve these before finalizing `manager_M1_report.md`:

1. `sub_S1/verify_enumeration_results.json` currently contains zero squares. Do not present this as a successful independent enumeration. Rerun/fix if practical, or explicitly label the script uncompleted/unverified and rely on a separately executed verifier.
2. `sub_S1/source_notes.md` says complement gives “440 complementary pairs among 880.” The independent M4 audit reports 352 D4 classes fixed by complement and 264 two-class orbits, hence 616 complement orbits total. Reconcile terminology and correct the count.
3. Distinguish `complement_pair` (source pairing-group/sentinel metadata) from `complement_id` (partner square ID). State the exact observed sentinel semantics.
4. Ensure exact structural counts come from an executed script and define whether “pandiagonal/panmagic,” “associative,” “compact 2×2,” and “most-perfect” predicates include wraparound.
5. Cite the coordinator audit as independent verification where useful: `../coordinator_dataset_audit.py` and `../coordinator_dataset_audit.json`.
6. `sub_S2/enumerate.py` incorrectly claims that fixing `grid[0]=1` yields one representative per D4 orbit. D4 moves corners only to corners, while value 1 is not a corner in many normal 4×4 classes (the local canonical CSV places 1 at noncorner indices for most rows). Do not use this enumeration as completeness evidence unless the symmetry-breaking condition is replaced with a valid one and the result independently checks 7,040/880.
