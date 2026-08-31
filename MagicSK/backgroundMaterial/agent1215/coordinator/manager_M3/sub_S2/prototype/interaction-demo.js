/**
 * Wires MomentExplorerState to a minimal demo UI with hash sync.
 */
(function () {
  "use strict";

  const S = window.MomentExplorerState;

  const DEMO_RECORDS = [
    { recordId: "M001", sourceId: 1, cohort: "magic", swaps: 0, dudeneyGroup: 6, classes: ["ordinary"], isMagic: true, spectralCentroid: 3.55, interactionEnergy: 340, lineDefectEnergy: 0, lowOrderEnergy: 230, highOrderEnergy: 110, cells: [1,2,15,16,12,14,3,5,13,7,10,4,8,11,6,9] },
    { recordId: "M002", sourceId: 2, cohort: "magic", swaps: 0, dudeneyGroup: 6, classes: ["ordinary"], isMagic: true, spectralCentroid: 3.60, interactionEnergy: 340, lineDefectEnergy: 0, lowOrderEnergy: 220, highOrderEnergy: 120, cells: [1,2,15,16,13,14,3,4,12,7,10,5,8,11,6,9] },
    { recordId: "M003", sourceId: 3, cohort: "magic", swaps: 0, dudeneyGroup: 12, classes: ["ordinary"], isMagic: true, spectralCentroid: 3.40, interactionEnergy: 340, lineDefectEnergy: 0, lowOrderEnergy: 210, highOrderEnergy: 130, cells: [1,2,16,15,13,14,4,3,12,7,9,6,8,11,5,10] },
    { recordId: "R001", sourceId: 1, cohort: "random", swaps: 0, dudeneyGroup: 6, classes: ["ordinary"], isMagic: false, spectralCentroid: 4.00, interactionEnergy: 300, lineDefectEnergy: 500, lowOrderEnergy: 60, highOrderEnergy: 240, cells: [5,1,12,16,3,9,14,8,11,7,2,15,10,13,4,6] },
    { recordId: "S101", sourceId: 1, cohort: "swap-1", swaps: 1, dudeneyGroup: 6, classes: ["ordinary"], isMagic: false, spectralCentroid: 3.90, interactionEnergy: 310, lineDefectEnergy: 100, lowOrderEnergy: 80, highOrderEnergy: 230, cells: [1,2,15,16,12,14,3,5,13,7,10,4,8,11,6,9] },
  ];

  let state = S.setLoadStatus(S.DEFAULT_STATE, "ready", { records: DEMO_RECORDS });
  let focusedId = null;
  let filterTrigger = null;
  let suppressHash = false;

  const el = {
    banner: document.getElementById("load-banner"),
    hash: document.getElementById("hash-out"),
    search: document.getElementById("f-search"),
    magic: document.getElementById("f-magic"),
    view: document.getElementById("f-view"),
    summary: document.getElementById("summary-dl"),
    resultsStatus: document.getElementById("results-status"),
    tbody: document.getElementById("results-body"),
    cards: document.getElementById("results-cards"),
    tableWrap: document.getElementById("results-table-wrap"),
    inspect: document.getElementById("inspect-panel"),
    compare: document.getElementById("compare-panel"),
  };

  function cohortsFromDom() {
    return [...document.querySelectorAll('input[name="cohort"]:checked')].map((n) => n.value);
  }

  function syncHash(replace) {
    const hash = S.serializeHash(state);
    el.hash.textContent = hash;
    if (suppressHash) return;
    if (replace) {
      history.replaceState(null, "", hash);
    }
  }

  function renderBanner() {
    const ui = S.uiStatus(state);
    el.banner.textContent = ui.message;
    el.banner.className = `banner ${ui.kind}`;
    el.resultsStatus.textContent = ui.message;
  }

  function renderSummary(summary) {
    el.summary.innerHTML = `
      <div><dt>Visible</dt><dd>${summary.count || "—"}</dd></div>
      <div><dt>Magic</dt><dd>${summary.count ? summary.magicCount : "—"}</dd></div>
      <div><dt>Mean centroid</dt><dd>${summary.meanCentroid != null ? summary.meanCentroid.toFixed(2) : "—"}</dd></div>
      <div><dt>Mean interaction E</dt><dd>${summary.meanInteraction != null ? summary.meanInteraction.toFixed(0) : "—"}</dd></div>`;
  }

  function miniSquare(cells) {
    return `<div class="mini-grid" aria-label="4 by 4 square">${cells.map((v) => `<span>${v}</span>`).join("")}</div>`;
  }

  function renderResults(results, selection) {
    if (state.view === "cards") {
      el.tableWrap.hidden = true;
      el.cards.hidden = false;
      el.cards.className = "card-grid";
      el.cards.innerHTML = results
        .map(
          (r) => `
        <article class="record-card ${selection.primary === r.recordId ? "is-primary" : ""}" tabindex="0" data-id="${r.recordId}">
          <strong>${r.recordId}</strong> · ${r.cohort}<br>
          centroid ${r.spectralCentroid.toFixed(2)}
          <div class="row-actions">
            <button type="button" data-inspect="${r.recordId}">Inspect</button>
            <button type="button" data-compare="${r.recordId}">Compare</button>
          </div>
        </article>`
        )
        .join("");
    } else {
      el.tableWrap.hidden = false;
      el.cards.hidden = true;
      el.tbody.innerHTML = results
        .map(
          (r) => `
        <tr data-id="${r.recordId}" class="${selection.primary === r.recordId ? "is-primary" : ""} ${focusedId === r.recordId ? "is-focused" : ""}" tabindex="-1">
          <th scope="row">${r.recordId}</th>
          <td>${r.cohort}</td>
          <td>${r.spectralCentroid.toFixed(2)}</td>
          <td class="row-actions">
            <button type="button" data-inspect="${r.recordId}">Inspect</button>
            <button type="button" data-compare="${r.recordId}">Compare</button>
          </td>
        </tr>`
        )
        .join("");
    }
  }

  function renderInspect(primary, results) {
    if (!primary) {
      el.inspect.className = "empty";
      el.inspect.textContent = "No selection";
      return;
    }
    const record = results.find((r) => r.recordId === primary) || state.records.find((r) => r.recordId === primary);
    if (!record) {
      el.inspect.className = "empty";
      el.inspect.textContent = "Selection not in filtered results";
      return;
    }
    el.inspect.className = "";
    el.inspect.innerHTML = `
      <h3>${record.recordId}</h3>
      <p>Group ${record.dudeneyGroup} · ${record.cohort} · magic=${record.isMagic}</p>
      ${miniSquare(record.cells)}
      <p>Interaction E: ${record.interactionEnergy}</p>`;
  }

  function renderCompare(compare, results) {
    if (compare.length < 2) {
      el.compare.className = "empty";
      el.compare.textContent = "Select 2+ records to compare";
      return;
    }
    el.compare.className = "compare-grid";
    el.compare.innerHTML = compare
      .map((id) => {
        const r = results.find((x) => x.recordId === id) || state.records.find((x) => x.recordId === id);
        if (!r) return "";
        return `<div class="compare-cell"><strong>${r.recordId}</strong><br>centroid ${r.spectralCentroid.toFixed(2)}<br>defect ${r.lineDefectEnergy}</div>`;
      })
      .join("");
  }

  function renderAll() {
    const { results, summary, selection } = S.derivePipeline(state);
    renderBanner();
    renderSummary(summary);
    renderResults(results, selection);
    renderInspect(selection.primary, results);
    renderCompare(selection.compare, results);
    syncHash(true);
  }

  function applyDomToState() {
    state = S.setFilters(state, {
      search: el.search.value,
      cohorts: cohortsFromDom(),
      magicOnly: el.magic.checked,
    });
    state.view = el.view.value;
    state = S.reconcileSelection(state);
    renderAll();
  }

  function restoreFocusAfterFilter() {
    if (filterTrigger && typeof filterTrigger.focus === "function") {
      filterTrigger.focus();
      filterTrigger = null;
    }
  }

  document.querySelectorAll('input[name="cohort"], #f-magic, #f-search, #f-view').forEach((node) => {
    node.addEventListener("change", () => {
      filterTrigger = document.activeElement;
      applyDomToState();
      restoreFocusAfterFilter();
    });
    node.addEventListener("input", () => {
      filterTrigger = document.activeElement;
      applyDomToState();
      restoreFocusAfterFilter();
    });
  });

  document.getElementById("btn-reset").addEventListener("click", () => {
    el.search.value = "";
    el.magic.checked = false;
    document.querySelectorAll('input[name="cohort"]').forEach((n) => {
      n.checked = n.value === "magic";
    });
    state = S.setFilters(state, { ...S.DEFAULT_FILTERS, cohorts: ["magic"] });
    state = S.setSort(state, [{ key: "recordId", dir: "asc" }]);
    state.selection = { primary: null, compare: [] };
    renderAll();
  });

  document.getElementById("btn-copy-link").addEventListener("click", () => {
    const hash = S.serializeHash(state);
    const url = `${location.origin}${location.pathname}${hash}`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url);
    } else {
      window.prompt("Copy this link:", url);
    }
  });

  document.querySelectorAll(".sort-btn").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      state = S.toggleSortKey(state, btn.dataset.key, { shift: event.shiftKey, defaultDir: "desc" });
      renderAll();
    });
  });

  function handleAction(event) {
    const inspect = event.target.closest("[data-inspect]");
    const compare = event.target.closest("[data-compare]");
    if (inspect) {
      state = S.setPrimarySelection(state, inspect.dataset.inspect);
      renderAll();
      document.getElementById("inspect-h").scrollIntoView({ block: "nearest" });
      return;
    }
    if (compare) {
      const res = S.toggleCompare(state, compare.dataset.compare);
      state = res.state;
      if (res.error) {
        el.resultsStatus.textContent = "Compare limited to 4 records.";
      }
      renderAll();
    }
  }

  el.tbody.addEventListener("click", handleAction);
  el.cards.addEventListener("click", handleAction);

  window.addEventListener("hashchange", () => {
    suppressHash = true;
    state = S.hydrateFromHash(state, location.hash);
    el.search.value = state.filters.search;
    el.magic.checked = state.filters.magicOnly;
    el.view.value = state.view;
    document.querySelectorAll('input[name="cohort"]').forEach((n) => {
      n.checked = state.filters.cohorts.length === 0 || state.filters.cohorts.includes(n.value);
    });
    renderAll();
    suppressHash = false;
  });

  document.addEventListener("keydown", (event) => {
    if (event.target.matches("input, select, textarea")) return;
    const { results, selection } = S.derivePipeline(state);
    if (!results.length) return;
    const idx = results.findIndex((r) => r.recordId === focusedId);
    if (event.key === "ArrowDown") {
      event.preventDefault();
      focusedId = results[Math.min(results.length - 1, idx < 0 ? 0 : idx + 1)].recordId;
      renderAll();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      focusedId = results[Math.max(0, idx < 0 ? 0 : idx - 1)].recordId;
      renderAll();
    } else if (event.key === "Enter" && focusedId) {
      state = S.setPrimarySelection(state, focusedId);
      renderAll();
    } else if (event.key === " " && focusedId) {
      event.preventDefault();
      const res = S.toggleCompare(state, focusedId);
      state = res.state;
      renderAll();
    }
  });

  if (location.hash) {
    state = S.hydrateFromHash(state, location.hash);
    el.search.value = state.filters.search;
    el.magic.checked = state.filters.magicOnly;
    el.view.value = state.view;
    document.querySelectorAll('input[name="cohort"]').forEach((n) => {
      n.checked = state.filters.cohorts.length === 0 || state.filters.cohorts.includes(n.value);
    });
  }

  renderAll();
})();
