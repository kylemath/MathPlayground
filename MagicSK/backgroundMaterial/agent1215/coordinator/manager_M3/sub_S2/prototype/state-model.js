/**
 * Magic Moment Explorer — dependency-free interaction state model (v1).
 * Pure functions; no DOM. Usable in browser or Node (tests).
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.MomentExplorerState = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const MAX_COMPARE = 4;
  const TIEBREAK_KEY = "recordId";

  /** Numeric fields permitted in filters.ranges and URL ?range= codec. */
  const ALLOWED_RANGE_KEYS = Object.freeze([
    "sourceId",
    "swaps",
    "dudeneyGroup",
    "spectralCentroid",
    "interactionEnergy",
    "lineDefectEnergy",
    "lowOrderEnergy",
    "highOrderEnergy",
  ]);

  const DEFAULT_FILTERS = Object.freeze({
    search: "",
    cohorts: [],
    groups: [],
    classes: [],
    classMode: "or",
    magicOnly: false,
    ranges: {},
  });

  const DEFAULT_STATE = Object.freeze({
    loadStatus: "idle",
    records: [],
    expectedCount: null,
    errorMessage: null,
    filters: { ...DEFAULT_FILTERS },
    sort: [{ key: "recordId", dir: "asc" }],
    view: "table",
    selection: { primary: null, compare: [] },
    focusedRecordId: null,
    lastFocusedControl: null,
  });

  function cloneState(state) {
    return {
      ...state,
      filters: { ...state.filters, cohorts: [...state.filters.cohorts], groups: [...state.filters.groups], classes: [...state.filters.classes], ranges: { ...state.filters.ranges } },
      sort: state.sort.map((s) => ({ ...s })),
      selection: { primary: state.selection.primary, compare: [...state.selection.compare] },
      records: state.records,
    };
  }

  function compareValues(a, b, dir) {
    const mul = dir === "desc" ? -1 : 1;
    const aNull = a === null || a === undefined || Number.isNaN(a);
    const bNull = b === null || b === undefined || Number.isNaN(b);
    if (aNull && bNull) return 0;
    // Null numerics: last in asc, first in desc.
    if (aNull) return dir === "desc" ? -1 : 1;
    if (bNull) return dir === "desc" ? 1 : -1;
    if (typeof a === "string" && typeof b === "string") {
      return mul * a.localeCompare(b, undefined, { numeric: true });
    }
    if (a < b) return -1 * mul;
    if (a > b) return 1 * mul;
    return 0;
  }

  function getField(record, key) {
    if (key === "recordId") return record.recordId;
    if (key === "sourceId") return record.sourceId;
    if (key === "cohort") return record.cohort;
    if (key === "dudeneyGroup") return record.dudeneyGroup;
    if (key === "swaps") return record.swaps;
    if (key === "isMagic") return record.isMagic ? 1 : 0;
    if (key === "spectralCentroid") return record.spectralCentroid;
    if (key === "interactionEnergy") return record.interactionEnergy;
    if (key === "lineDefectEnergy") return record.lineDefectEnergy;
    if (key === "lowOrderEnergy") return record.lowOrderEnergy;
    if (key === "highOrderEnergy") return record.highOrderEnergy;
    return record[key];
  }

  /**
   * Append recordId ascending only when sort does not already name recordId.
   * An explicit recordId key (asc or desc) is a complete unique ordering.
   */
  function ensureTiebreak(sort) {
    const keys = sort.map((s) => s.key);
    if (keys.includes(TIEBREAK_KEY)) return sort.map((s) => ({ ...s }));
    return [...sort.map((s) => ({ ...s })), { key: TIEBREAK_KEY, dir: "asc" }];
  }

  function encodeRanges(ranges) {
    if (!ranges || typeof ranges !== "object") return "";
    return Object.keys(ranges)
      .filter((key) => ALLOWED_RANGE_KEYS.includes(key))
      .sort()
      .map((key) => {
        const spec = ranges[key];
        if (!spec || typeof spec !== "object") return null;
        const lo = spec.min !== undefined && spec.min !== null ? String(spec.min) : "";
        const hi = spec.max !== undefined && spec.max !== null ? String(spec.max) : "";
        if (!lo && !hi) return null;
        return `${key}:${lo}~${hi}`;
      })
      .filter(Boolean)
      .join(",");
  }

  function decodeRanges(raw) {
    if (!raw) return {};
    const out = {};
    splitList(raw).forEach((segment) => {
      const colon = segment.indexOf(":");
      if (colon < 0) return;
      const key = segment.slice(0, colon);
      if (!ALLOWED_RANGE_KEYS.includes(key)) return;
      const [loRaw, hiRaw = ""] = segment.slice(colon + 1).split("~");
      const range = {};
      if (loRaw !== "") {
        const min = Number(loRaw);
        if (!Number.isNaN(min)) range.min = min;
      }
      if (hiRaw !== "") {
        const max = Number(hiRaw);
        if (!Number.isNaN(max)) range.max = max;
      }
      if (range.min !== undefined || range.max !== undefined) out[key] = range;
    });
    return out;
  }

  function stableMultiSort(records, sort) {
    const keys = ensureTiebreak(sort);
    const indexed = records.map((record, index) => ({ record, index }));
    indexed.sort((left, right) => {
      for (const { key, dir } of keys) {
        const cmp = compareValues(getField(left.record, key), getField(right.record, key), dir);
        if (cmp !== 0) return cmp;
      }
      return left.index - right.index;
    });
    return indexed.map((item) => item.record);
  }

  function matchesSearch(record, search) {
    if (!search) return true;
    const q = search.trim().toLowerCase();
    if (!q) return true;
    if (record.recordId.toLowerCase().startsWith(q)) return true;
    if (String(record.sourceId) === q) return true;
    return false;
  }

  function matchesRanges(record, ranges) {
    for (const [field, range] of Object.entries(ranges)) {
      const value = getField(record, field);
      if (range.min !== undefined && value < range.min) return false;
      if (range.max !== undefined && value > range.max) return false;
    }
    return true;
  }

  function matchesClasses(record, classes, mode) {
    if (!classes.length) return true;
    const tags = record.classes || [];
    if (mode === "and") return classes.every((c) => tags.includes(c));
    return classes.some((c) => tags.includes(c));
  }

  function applyFilters(records, filters) {
    return records.filter((record) => {
      if (!matchesSearch(record, filters.search)) return false;
      if (filters.cohorts.length && !filters.cohorts.includes(record.cohort)) return false;
      if (filters.groups.length && !filters.groups.includes(record.dudeneyGroup)) return false;
      if (!matchesClasses(record, filters.classes, filters.classMode)) return false;
      if (filters.magicOnly && !record.isMagic) return false;
      if (!matchesRanges(record, filters.ranges)) return false;
      return true;
    });
  }

  function computeSummary(filtered) {
    if (!filtered.length) {
      return {
        count: 0,
        magicCount: 0,
        meanInteraction: null,
        meanCentroid: null,
        meanLineDefect: null,
        dudeneyCounts: {},
        cohortCounts: {},
        classCounts: {},
      };
    }
    let sumInteraction = 0;
    let sumCentroid = 0;
    let sumLineDefect = 0;
    let magicCount = 0;
    const dudeneyCounts = {};
    const cohortCounts = {};
    const classCounts = {};

    filtered.forEach((record) => {
      sumInteraction += record.interactionEnergy;
      sumCentroid += record.spectralCentroid;
      sumLineDefect += record.lineDefectEnergy;
      if (record.isMagic) magicCount += 1;
      dudeneyCounts[record.dudeneyGroup] = (dudeneyCounts[record.dudeneyGroup] || 0) + 1;
      cohortCounts[record.cohort] = (cohortCounts[record.cohort] || 0) + 1;
      (record.classes || []).forEach((tag) => {
        classCounts[tag] = (classCounts[tag] || 0) + 1;
      });
    });

    const n = filtered.length;
    return {
      count: n,
      magicCount,
      meanInteraction: sumInteraction / n,
      meanCentroid: sumCentroid / n,
      meanLineDefect: sumLineDefect / n,
      dudeneyCounts,
      cohortCounts,
      classCounts,
    };
  }

  function derivePipeline(state) {
    const filtered = applyFilters(state.records, state.filters);
    const results = stableMultiSort(filtered, state.sort);
    const summary = computeSummary(filtered);
    const visibleIds = new Set(results.map((r) => r.recordId));
    const primary = state.selection.primary && visibleIds.has(state.selection.primary)
      ? state.selection.primary
      : null;
    const compare = state.selection.compare.filter((id) => visibleIds.has(id)).slice(0, MAX_COMPARE);
    return { filtered, results, summary, selection: { primary, compare } };
  }

  function setLoadStatus(state, loadStatus, extras = {}) {
    const next = cloneState(state);
    next.loadStatus = loadStatus;
    if (extras.records) next.records = extras.records;
    if (extras.expectedCount !== undefined) next.expectedCount = extras.expectedCount;
    if (extras.errorMessage !== undefined) next.errorMessage = extras.errorMessage;
    return next;
  }

  function setFilters(state, patch) {
    const next = cloneState(state);
    next.filters = { ...next.filters, ...patch };
    return reconcileSelection(next);
  }

  function setSort(state, sort) {
    const next = cloneState(state);
    next.sort = sort.length ? sort.map((s) => ({ ...s })) : [{ key: TIEBREAK_KEY, dir: "asc" }];
    return next;
  }

  function toggleSortKey(state, key, { shift = false, defaultDir = "asc" } = {}) {
    const next = cloneState(state);
    const existing = next.sort.find((s) => s.key === key);
    if (!shift) {
      if (existing) {
        next.sort = [{ key, dir: existing.dir === "asc" ? "desc" : "asc" }];
      } else {
        next.sort = [{ key, dir: defaultDir }];
      }
      return next;
    }
    if (existing) {
      next.sort = next.sort.map((s) =>
        s.key === key ? { ...s, dir: s.dir === "asc" ? "desc" : "asc" } : s
      );
    } else {
      next.sort.push({ key, dir: defaultDir });
    }
    return next;
  }

  function setPrimarySelection(state, recordId) {
    const next = cloneState(state);
    next.selection.primary = recordId;
    return next;
  }

  function toggleCompare(state, recordId) {
    const next = cloneState(state);
    const set = new Set(next.selection.compare);
    if (set.has(recordId)) {
      set.delete(recordId);
    } else {
      if (set.size >= MAX_COMPARE) {
        return { state: next, error: "compare_limit" };
      }
      set.add(recordId);
    }
    next.selection.compare = [...set];
    return { state: next, error: null };
  }

  function reconcileSelection(state) {
    const { selection } = derivePipeline(state);
    const next = cloneState(state);
    next.selection.primary = selection.primary;
    next.selection.compare = selection.compare;
    return next;
  }

  function parseHash(hash) {
    const raw = hash.replace(/^#\/?/, "");
    const query = raw.includes("?") ? raw.split("?")[1] : raw;
    const params = new URLSearchParams(query);
    const sortRaw = params.get("sort");
    const sort = sortRaw
      ? sortRaw.split(",").map((pair) => {
          const [key, dir] = pair.split(":");
          return { key, dir: dir === "desc" ? "desc" : "asc" };
        })
      : null;

    return {
      cohorts: splitList(params.get("cohort")),
      groups: splitList(params.get("group")).map(Number).filter((n) => !Number.isNaN(n)),
      classes: splitList(params.get("class")),
      classMode: params.get("classMode") === "and" ? "and" : "or",
      magicOnly: params.get("magic") === "1",
      search: params.get("q") || "",
      ranges: decodeRanges(params.get("range")),
      sort,
      primary: params.get("sel") || null,
      compare: splitList(params.get("compare")),
      view: params.get("view") === "cards" ? "cards" : "table",
    };
  }

  function splitList(value) {
    if (!value) return [];
    return value.split(",").map((s) => s.trim()).filter(Boolean);
  }

  function serializeHash(state) {
    const f = state.filters;
    const params = new URLSearchParams();
    if (f.search) params.set("q", f.search);
    if (f.cohorts.length) params.set("cohort", f.cohorts.join(","));
    if (f.groups.length) params.set("group", f.groups.join(","));
    if (f.classes.length) params.set("class", f.classes.join(","));
    if (f.classMode === "and") params.set("classMode", "and");
    if (f.magicOnly) params.set("magic", "1");
    const rangeStr = encodeRanges(f.ranges);
    if (rangeStr) params.set("range", rangeStr);
    const sortStr = ensureTiebreak(state.sort)
      .filter((s) => s.key !== TIEBREAK_KEY || state.sort.some((x) => x.key === TIEBREAK_KEY))
      .map((s) => `${s.key}:${s.dir}`)
      .join(",");
    if (sortStr) params.set("sort", sortStr);
    if (state.selection.primary) params.set("sel", state.selection.primary);
    if (state.selection.compare.length) params.set("compare", state.selection.compare.join(","));
    if (state.view === "cards") params.set("view", "cards");
    const qs = params.toString();
    return qs ? `#/browse?${qs}` : "#/browse";
  }

  function hydrateFromHash(state, hash) {
    const parsed = parseHash(hash);
    let next = cloneState(state);
    next.filters = {
      ...next.filters,
      search: parsed.search,
      cohorts: parsed.cohorts,
      groups: parsed.groups,
      classes: parsed.classes,
      classMode: parsed.classMode,
      magicOnly: parsed.magicOnly,
      ranges: parsed.ranges,
    };
    if (parsed.sort) next.sort = parsed.sort;
    next.view = parsed.view;
    next.selection.primary = parsed.primary;
    next.selection.compare = parsed.compare.slice(0, MAX_COMPARE);
    return reconcileSelection(next);
  }

  function uiStatus(state) {
    const { results, summary } = derivePipeline(state);
    if (state.loadStatus === "loading") return { kind: "loading", message: "Loading dataset…" };
    if (state.loadStatus === "error") {
      return { kind: "error", message: state.errorMessage || "Failed to load dataset." };
    }
    if (state.loadStatus === "idle") return { kind: "idle", message: "Load a dataset to begin." };
    if (state.loadStatus === "partial") {
      return {
        kind: "partial",
        message: `Loaded ${state.records.length} of ${state.expectedCount} records. Filters apply to loaded subset.`,
      };
    }
    if (!results.length) {
      return { kind: "empty", message: "No records match the current filters." };
    }
    return { kind: "ready", message: `Showing ${summary.count} records.` };
  }

  return {
    MAX_COMPARE,
    TIEBREAK_KEY,
    ALLOWED_RANGE_KEYS,
    DEFAULT_STATE,
    DEFAULT_FILTERS,
    applyFilters,
    stableMultiSort,
    computeSummary,
    derivePipeline,
    setLoadStatus,
    setFilters,
    setSort,
    toggleSortKey,
    setPrimarySelection,
    toggleCompare,
    reconcileSelection,
    parseHash,
    serializeHash,
    hydrateFromHash,
    encodeRanges,
    decodeRanges,
    uiStatus,
    getField,
    compareValues,
    ensureTiebreak,
  };
});
