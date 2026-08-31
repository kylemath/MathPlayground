# Coordinator Review Notes for M3

Please resolve these before finalizing `manager_M3_report.md`:

1. Do not call all 15 non-DC tensor modes “interaction modes.” Six are nonconstant axial modes (`a=0 xor b=0`); only nine have `a,b>0`.
2. Reconcile the provisional schema with M1/M2 final definitions. In particular, document the exact `complement_pair` versus `complement_id` semantics, include basis vectors or a regeneration recipe, and avoid silently rounding coefficients so far that browser Parseval checks drift.
3. The requested primary dataset is 880 canonical squares. A 4,400-record payload (880 each for baseline/random/swap1/swap2/swap3) is one possible expanded design, not the only schema. Recommend a compact primary bundle with aggregate controls and an optional detailed bundle.
4. A class bitfield is compact but brittle. Include a versioned flag registry and/or string-table representation so new nonexclusive structural classes do not require ambiguous client changes.
5. Clearly separate automated static-contract checks from actual browser, keyboard, and assistive-technology tests. Do not claim end-to-end accessibility from Node string/DOM-contract checks alone.
6. Verify all links and prototype assumptions are confined to the orchestration folder and do not depend on transient main-application files.
