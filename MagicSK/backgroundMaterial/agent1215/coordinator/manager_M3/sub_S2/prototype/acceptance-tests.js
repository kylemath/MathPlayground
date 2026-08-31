/**
 * Acceptance tests for MomentExplorerState.
 * Run: node acceptance-tests.js
 * Or open acceptance-tests.html in a browser.
 */
(function (root, factory) {
  const tests = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = tests;
  } else {
    root.runAcceptanceTests = tests.run;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const S = require("./state-model.js");

  const FIXTURE = [
    {
      recordId: "M001",
      sourceId: 1,
      cohort: "magic",
      swaps: 0,
      dudeneyGroup: 6,
      classes: ["ordinary"],
      isMagic: true,
      spectralCentroid: 3.5,
      interactionEnergy: 340,
      lineDefectEnergy: 0,
      lowOrderEnergy: 230,
      highOrderEnergy: 110,
    },
    {
      recordId: "M002",
      sourceId: 2,
      cohort: "magic",
      swaps: 0,
      dudeneyGroup: 6,
      classes: ["ordinary"],
      isMagic: true,
      spectralCentroid: 3.6,
      interactionEnergy: 340,
      lineDefectEnergy: 0,
      lowOrderEnergy: 220,
      highOrderEnergy: 120,
    },
    {
      recordId: "M003",
      sourceId: 3,
      cohort: "magic",
      swaps: 0,
      dudeneyGroup: 12,
      classes: ["ordinary"],
      isMagic: true,
      spectralCentroid: 3.4,
      interactionEnergy: 340,
      lineDefectEnergy: 0,
      lowOrderEnergy: 210,
      highOrderEnergy: 130,
    },
    {
      recordId: "R001",
      sourceId: 1,
      cohort: "random",
      swaps: 0,
      dudeneyGroup: 6,
      classes: ["ordinary"],
      isMagic: false,
      spectralCentroid: 4.0,
      interactionEnergy: 300,
      lineDefectEnergy: 500,
      lowOrderEnergy: 60,
      highOrderEnergy: 240,
    },
    {
      recordId: "S101",
      sourceId: 1,
      cohort: "swap-1",
      swaps: 1,
      dudeneyGroup: 6,
      classes: ["ordinary"],
      isMagic: false,
      spectralCentroid: 3.9,
      interactionEnergy: 310,
      lineDefectEnergy: 100,
      lowOrderEnergy: 80,
      highOrderEnergy: 230,
    },
  ];

  function assert(condition, message) {
    if (!condition) throw new Error(message);
  }

  function test(name, fn) {
    try {
      fn();
      return { name, pass: true };
    } catch (err) {
      return { name, pass: false, error: err.message };
    }
  }

  function run() {
    const results = [];

    results.push(
      test("combined filters AND across cohort and magic", () => {
        const state = S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: FIXTURE });
        const filtered = S.applyFilters(state.records, {
          ...S.DEFAULT_FILTERS,
          cohorts: ["magic"],
          magicOnly: true,
        });
        assert(filtered.length === 3, `expected 3 magic, got ${filtered.length}`);
      })
    );

    results.push(
      test("class OR mode matches any selected tag", () => {
        const records = [
          { ...FIXTURE[0], classes: ["pandiagonal"] },
          { ...FIXTURE[1], classes: ["ordinary"] },
        ];
        const filtered = S.applyFilters(records, {
          ...S.DEFAULT_FILTERS,
          classes: ["pandiagonal", "ordinary"],
          classMode: "or",
        });
        assert(filtered.length === 2, "OR should keep both");
      })
    );

    results.push(
      test("compareValues nulls last in asc, first in desc", () => {
        assert(S.compareValues(null, 1, "asc") > 0, "null last in asc");
        assert(S.compareValues(1, null, "asc") < 0, "non-null before null in asc");
        assert(S.compareValues(null, 1, "desc") < 0, "null first in desc");
        assert(S.compareValues(1, null, "desc") > 0, "non-null after null in desc");
      })
    );

    results.push(
      test("null numeric sort order in stableMultiSort", () => {
        const records = [
          { ...FIXTURE[0], recordId: "A", spectralCentroid: 3.0 },
          { ...FIXTURE[1], recordId: "B", spectralCentroid: null },
          { ...FIXTURE[2], recordId: "C", spectralCentroid: 4.0 },
        ];
        const asc = S.stableMultiSort(records, [{ key: "spectralCentroid", dir: "asc" }]);
        assert(asc.map((r) => r.recordId).join(",") === "A,C,B", "null last ascending");
        const desc = S.stableMultiSort(records, [{ key: "spectralCentroid", dir: "desc" }]);
        assert(desc.map((r) => r.recordId).join(",") === "B,C,A", "null first descending");
      })
    );

    results.push(
      test("explicit recordId sort does not append tie-breaker", () => {
        const keys = S.ensureTiebreak([{ key: "recordId", dir: "desc" }]).map((s) => s.key);
        assert(keys.length === 1 && keys[0] === "recordId", "no duplicate recordId");
        const sorted = S.stableMultiSort(FIXTURE.slice(0, 3), [{ key: "recordId", dir: "desc" }]);
        assert(sorted[0].recordId === "M003", "desc recordId is complete order");
      })
    );

    results.push(
      test("implicit recordId asc tie-breaker when absent", () => {
        const keys = S.ensureTiebreak([{ key: "dudeneyGroup", dir: "asc" }]).map((s) => s.key);
        assert(keys[keys.length - 1] === "recordId", "appends recordId asc");
        assert(keys[keys.length - 2] === "dudeneyGroup", "preserves primary key");
      })
    );

    results.push(
      test("stable multi-key sort orders by secondary key then recordId", () => {
        const sorted = S.stableMultiSort(FIXTURE.slice(0, 3), [
          { key: "dudeneyGroup", dir: "asc" },
          { key: "spectralCentroid", dir: "desc" },
        ]);
        assert(sorted[0].recordId === "M002", "M002 first in group 6 (higher centroid)");
        assert(sorted[1].recordId === "M001", "M001 second in group 6");
        assert(sorted[2].recordId === "M003", "M003 group 12 last");
      })
    );

    results.push(
      test("sort stability preserves input order on full tie", () => {
        const tied = FIXTURE.slice(0, 2).map((r) => ({ ...r, spectralCentroid: 3.5 }));
        const sorted = S.stableMultiSort(tied, [{ key: "spectralCentroid", dir: "asc" }]);
        assert(sorted[0].recordId === "M001" && sorted[1].recordId === "M002", "stable order");
      })
    );

    results.push(
      test("compare enforces max four", () => {
        let state = S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: FIXTURE });
        const ids = ["M001", "M002", "M003", "R001", "S101"];
        let err = null;
        ids.forEach((id) => {
          const res = S.toggleCompare(state, id);
          state = res.state;
          if (res.error) err = res.error;
        });
        assert(err === "compare_limit", "fifth compare rejected");
        assert(state.selection.compare.length === 4, "only four stored");
      })
    );

    results.push(
      test("filter change drops invisible primary selection", () => {
        let state = S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: FIXTURE });
        state = S.setPrimarySelection(state, "R001");
        state = S.setFilters(state, { cohorts: ["magic"] });
        const { selection } = S.derivePipeline(state);
        assert(selection.primary === null, "R001 not in magic cohort");
      })
    );

    results.push(
      test("encodeRanges is deterministic and validates keys", () => {
        const encoded = S.encodeRanges({
          spectralCentroid: { min: 3.4, max: 4.0 },
          bogusField: { min: 0, max: 1 },
          interactionEnergy: { min: 300 },
        });
        assert(encoded === "interactionEnergy:300~,spectralCentroid:3.4~4", "sorted allowed keys only");
        const decoded = S.decodeRanges(encoded + ",notAllowed:1~2");
        assert(decoded.spectralCentroid.min === 3.4, "min");
        assert(decoded.spectralCentroid.max === 4, "max");
        assert(decoded.interactionEnergy.min === 300, "open max");
        assert(decoded.notAllowed === undefined, "rejects unknown key");
      })
    );

    results.push(
      test("URL hash round-trip preserves numeric ranges", () => {
        let state = S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: FIXTURE });
        state = S.setFilters(state, {
          ranges: {
            spectralCentroid: { min: 3.5, max: 3.9 },
            lineDefectEnergy: { max: 100 },
          },
        });
        const hash = S.serializeHash(state);
        assert(hash.includes("range="), "range param present");
        const restored = S.hydrateFromHash(state, hash);
        assert(restored.filters.ranges.spectralCentroid.min === 3.5, "centroid min");
        assert(restored.filters.ranges.spectralCentroid.max === 3.9, "centroid max");
        assert(restored.filters.ranges.lineDefectEnergy.max === 100, "defect max");
        const filtered = S.applyFilters(state.records, restored.filters);
        assert(filtered.every((r) => r.spectralCentroid >= 3.5 && r.spectralCentroid <= 3.9), "range filters apply");
      })
    );

    results.push(
      test("URL hash round-trip preserves filters sort and selection", () => {
        let state = S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: FIXTURE });
        state = S.setFilters(state, {
          cohorts: ["magic", "swap-1"],
          groups: [6, 12],
          classes: ["ordinary"],
          magicOnly: false,
          search: "M00",
        });
        state = S.setSort(state, [
          { key: "spectralCentroid", dir: "desc" },
          { key: "dudeneyGroup", dir: "asc" },
        ]);
        state = S.setPrimarySelection(state, "M002");
        state.selection.compare = ["M001", "M003"];
        const hash = S.serializeHash(state);
        const restored = S.hydrateFromHash(state, hash);
        assert(restored.filters.cohorts.join(",") === "magic,swap-1", "cohorts");
        assert(restored.sort[0].key === "spectralCentroid", "sort key");
        assert(restored.selection.primary === "M002", "primary");
        assert(restored.selection.compare.length === 2, "compare");
      })
    );

    results.push(
      test("empty filter results yield empty ui status", () => {
        const state = S.setLoadStatus(
          S.setFilters(S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: FIXTURE }), {
            search: "ZZZZZ",
          }),
          "ready",
          { records: FIXTURE }
        );
        const status = S.uiStatus(state);
        assert(status.kind === "empty", `expected empty got ${status.kind}`);
      })
    );

    results.push(
      test("partial load status surfaces banner kind", () => {
        const state = S.setLoadStatus(S.DEFAULT_STATE, "partial", {
          records: FIXTURE,
          expectedCount: 4400,
        });
        const status = S.uiStatus(state);
        assert(status.kind === "partial", "partial banner");
        assert(status.message.includes("4400"), "mentions expected count");
      })
    );

    results.push(
      test("summary aggregates respect filtered set only", () => {
        const state = S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: FIXTURE });
        const { summary } = S.derivePipeline(
          S.setFilters(state, { cohorts: ["magic"] })
        );
        assert(summary.count === 3, "three magic");
        assert(summary.magicCount === 3, "all magic");
        assert(summary.dudeneyCounts[6] === 2, "two in group 6");
      })
    );

    const passed = results.filter((r) => r.pass).length;
    const failed = results.filter((r) => !r.pass);
    return { passed, total: results.length, failed, results };
  }

  if (require.main === module) {
    const out = run();
    console.log(`Acceptance tests: ${out.passed}/${out.total} passed`);
    out.failed.forEach((f) => console.error(`FAIL ${f.name}: ${f.error}`));
    process.exit(out.failed.length ? 1 : 0);
  }

  return { run };
});
