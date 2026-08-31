/**
 * Main application: filtering, stable sorting, summaries, selection, comparison, UI states.
 */
(function () {
  "use strict";

  const state = {
    allRecords: [],
    filtered: [],
    selectedId: null,
    compareIds: [],
    sortKey: "recordId",
    sortDir: "asc",
    loading: false,
    error: null,
    schemaMeta: null,
  };

  const els = {
    schemaBadge: document.getElementById("schema-badge"),
    datasetStatus: document.getElementById("dataset-status"),
    searchInput: document.getElementById("search-input"),
    cohortSelect: document.getElementById("cohort-select"),
    groupSelect: document.getElementById("group-select"),
    magicOnly: document.getElementById("magic-only"),
    sortSelect: document.getElementById("sort-select"),
    resetFilters: document.getElementById("reset-filters"),
    demoLoading: document.getElementById("demo-loading"),
    demoError: document.getElementById("demo-error"),
    reloadData: document.getElementById("reload-data"),
    statCount: document.getElementById("stat-count"),
    statMagic: document.getElementById("stat-magic"),
    statInteraction: document.getElementById("stat-interaction"),
    statCentroid: document.getElementById("stat-centroid"),
    groupSummary: document.getElementById("group-summary"),
    recordTbody: document.getElementById("record-tbody"),
    listState: document.getElementById("list-state"),
    detailEmpty: document.getElementById("detail-empty"),
    detailContent: document.getElementById("detail-content"),
    detailMeta: document.getElementById("detail-meta"),
    squareDiagram: document.getElementById("square-diagram"),
    lineSumsTable: document.getElementById("line-sums-table"),
    energyViz: document.getElementById("energy-viz"),
    compareEmpty: document.getElementById("compare-empty"),
    compareContent: document.getElementById("compare-content"),
  };

  let diagramController = null;

  function setStatus(message, kind = "success") {
    els.datasetStatus.textContent = message;
    els.datasetStatus.className = `status-banner ${kind}`;
  }

  function stableSort(records, key, dir) {
    const mult = dir === "desc" ? -1 : 1;
    return [...records].sort((a, b) => {
      let av = a[key];
      let bv = b[key];
      if (typeof av === "string") av = av.toLowerCase();
      if (typeof bv === "string") bv = bv.toLowerCase();
      if (av < bv) return -1 * mult;
      if (av > bv) return 1 * mult;
      return a.recordId.localeCompare(b.recordId);
    });
  }

  function parseSortValue(value) {
    if (value.includes("-")) {
      const [key, dir] = value.split("-");
      return { key, dir };
    }
    return { key: value, dir: "asc" };
  }

  function getSelectedClasses() {
    return [...document.querySelectorAll('input[name="class-filter"]:checked')].map(
      (input) => input.value
    );
  }

  function applyFilters() {
    const search = els.searchInput.value.trim().toLowerCase();
    const cohort = els.cohortSelect.value;
    const group = els.groupSelect.value;
    const magicOnly = els.magicOnly.checked;
    const classes = new Set(getSelectedClasses());

    let filtered = state.allRecords.filter((record) => {
      if (search && !record.recordId.toLowerCase().includes(search)) return false;
      if (cohort !== "all" && record.cohort !== cohort) return false;
      if (group !== "all" && String(record.dudeneyGroup) !== group) return false;
      if (magicOnly && !record.isMagic) return false;
      if (!record.classes.some((c) => classes.has(c))) return false;
      return true;
    });

    filtered = stableSort(filtered, state.sortKey, state.sortDir);
    state.filtered = filtered;
    renderAll();
  }

  function populateGroupOptions() {
    const groups = [...new Set(state.allRecords.map((r) => r.dudeneyGroup).filter(Boolean))].sort(
      (a, b) => a - b
    );
    els.groupSelect.innerHTML = '<option value="all">All groups</option>';
    groups.forEach((g) => {
      const opt = document.createElement("option");
      opt.value = String(g);
      opt.textContent = `Group ${g}`;
      els.groupSelect.appendChild(opt);
    });

    const cohorts = [...new Set(state.allRecords.map((r) => r.cohort))].sort();
    els.cohortSelect.innerHTML = '<option value="all">All cohorts</option>';
    cohorts.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      els.cohortSelect.appendChild(opt);
    });
  }

  function renderSummary() {
    const records = state.filtered;
    els.statCount.textContent = String(records.length);
    els.statMagic.textContent = String(records.filter((r) => r.isMagic).length);
    if (records.length === 0) {
      els.statInteraction.textContent = "—";
      els.statCentroid.textContent = "—";
      els.groupSummary.innerHTML = "";
      return;
    }
    const mean = (key) =>
      records.reduce((sum, r) => sum + Number(r[key] || 0), 0) / records.length;
    els.statInteraction.textContent = mean("interactionEnergy").toFixed(2);
    els.statCentroid.textContent = mean("spectralCentroid").toFixed(3);

    const groupCounts = {};
    records.forEach((r) => {
      const g = r.dudeneyGroup ?? "—";
      groupCounts[g] = (groupCounts[g] || 0) + 1;
    });
    els.groupSummary.innerHTML = Object.entries(groupCounts)
      .sort((a, b) => String(a[0]).localeCompare(String(b[0])))
      .map(([g, n]) => `<span class="group-chip">G${g}: ${n}</span>`)
      .join("");
  }

  function renderList() {
    els.recordTbody.innerHTML = "";
    els.listState.hidden = true;

    if (state.loading) {
      els.listState.hidden = false;
      els.listState.className = "list-state loading";
      els.listState.textContent = "Loading records…";
      return;
    }

    if (state.error) {
      els.listState.hidden = false;
      els.listState.className = "list-state error";
      els.listState.textContent = state.error;
      return;
    }

    if (state.filtered.length === 0) {
      els.listState.hidden = false;
      els.listState.className = "list-state";
      els.listState.textContent = "No records match the current filters (empty state).";
      return;
    }

    state.filtered.forEach((record) => {
      const tr = document.createElement("tr");
      if (record.recordId === state.selectedId) tr.classList.add("is-active");
      const compareChecked = state.compareIds.includes(record.recordId) ? "checked" : "";
      tr.innerHTML = `
        <td>
          <label class="visually-hidden" for="cmp-${record.recordId}">Compare ${record.recordId}</label>
          <input type="checkbox" id="cmp-${record.recordId}" data-compare="${record.recordId}" ${compareChecked}>
        </td>
        <th scope="row">${record.recordId}</th>
        <td>${record.cohort}</td>
        <td>${record.dudeneyGroup ?? "—"}</td>
        <td>${(record.classes || []).join(", ")}</td>
        <td>${Number(record.interactionEnergy).toFixed(2)}</td>
        <td>${Number(record.spectralCentroid).toFixed(3)}</td>
        <td><button type="button" class="primary inspect-btn" data-id="${record.recordId}">Inspect</button></td>`;
      els.recordTbody.appendChild(tr);
    });

    els.recordTbody.querySelectorAll(".inspect-btn").forEach((btn) => {
      btn.addEventListener("click", () => selectRecord(btn.dataset.id));
    });

    els.recordTbody.querySelectorAll("[data-compare]").forEach((input) => {
      input.addEventListener("change", () => toggleCompare(input.dataset.compare, input.checked));
    });
  }

  function selectRecord(recordId) {
    state.selectedId = recordId;
    renderList();
    renderDetail();
  }

  function toggleCompare(recordId, checked) {
    if (checked) {
      if (!state.compareIds.includes(recordId)) {
        if (state.compareIds.length >= 2) state.compareIds.shift();
        state.compareIds.push(recordId);
      }
    } else {
      state.compareIds = state.compareIds.filter((id) => id !== recordId);
    }
    renderList();
    renderCompare();
  }

  function renderDetail() {
    const record = state.allRecords.find((r) => r.recordId === state.selectedId);
    if (!record) {
      els.detailEmpty.hidden = false;
      els.detailContent.hidden = true;
      return;
    }

    els.detailEmpty.hidden = true;
    els.detailContent.hidden = false;
    els.detailMeta.innerHTML = `
      <div><span>Record:</span> <strong>${record.recordId}</strong> · cohort ${record.cohort} · ${record.dudeneyLabel || "—"}</div>
      <div><span>Classes:</span> ${(record.classes || []).join(", ")} · D4 orbit ${record.d4OrbitSize} · swaps ${record.swaps}</div>
      <div><span>Complement:</span> pair ${record.complementPair}, id ${record.complementId}, self ${record.selfComplementary ? "yes" : "no"}</div>`;

    diagramController = SquareDiagram.createDiagram(els.squareDiagram, record);
    SquareDiagram.renderLineSumsTable(els.lineSumsTable, record);
    EnergyViz.render(els.energyViz, record);
  }

  function renderCompare() {
    if (state.compareIds.length === 0) {
      els.compareEmpty.hidden = false;
      els.compareContent.hidden = true;
      return;
    }

    els.compareEmpty.hidden = true;
    els.compareContent.hidden = false;
    els.compareContent.innerHTML = state.compareIds
      .map((id) => {
        const r = state.allRecords.find((rec) => rec.recordId === id);
        if (!r) return "";
        return `<article class="compare-card" aria-label="Comparison for ${r.recordId}">
          <h3>${r.recordId}</h3>
          <dl class="compare-metrics">
            <dt>Cohort / group</dt><dd>${r.cohort} · G${r.dudeneyGroup ?? "—"}</dd>
            <dt>Interaction energy</dt><dd>${Number(r.interactionEnergy).toFixed(3)}</dd>
            <dt>Low / high order</dt><dd>${Number(r.lowOrderEnergy).toFixed(2)} / ${Number(r.highOrderEnergy).toFixed(2)}</dd>
            <dt>Spectral centroid</dt><dd>${Number(r.spectralCentroid).toFixed(4)}</dd>
            <dt>Line defect</dt><dd>${Number(r.lineDefectEnergy).toFixed(3)}</dd>
            <dt>Classes</dt><dd>${(r.classes || []).join(", ")}</dd>
          </dl>
        </article>`;
      })
      .join("");
  }

  function renderAll() {
    renderSummary();
    renderList();
    renderDetail();
    renderCompare();
  }

  async function loadData(options = {}) {
    state.loading = true;
    state.error = null;
    renderList();
    setStatus("Loading dataset…", "loading");

    try {
      const payload = await RecordDataLoader.loadDataset(options);
      state.allRecords = payload.records;
      state.schemaMeta = payload.metadata || {};
      state.loading = false;

      const serve = RecordDataLoader.describeServeMode();
      els.schemaBadge.textContent = `schema ${payload.schemaVersion} · ${state.allRecords.length} records · ${serve.mode}`;
      setStatus(
        `Loaded ${state.allRecords.length} records (${serve.mode} mode). ${serve.note}`,
        "success"
      );

      populateGroupOptions();
      applyFilters();
    } catch (error) {
      state.loading = false;
      state.error = error.message || String(error);
      state.allRecords = [];
      state.filtered = [];
      setStatus(state.error, "error");
      renderAll();
    }
  }

  function wireEvents() {
    [
      els.searchInput,
      els.cohortSelect,
      els.groupSelect,
      els.magicOnly,
      els.sortSelect,
    ].forEach((el) => el.addEventListener("input", applyFilters));
    els.magicOnly.addEventListener("change", applyFilters);

    document.querySelectorAll('input[name="class-filter"]').forEach((input) => {
      input.addEventListener("change", applyFilters);
    });

    els.sortSelect.addEventListener("change", () => {
      const parsed = parseSortValue(els.sortSelect.value);
      state.sortKey = parsed.key;
      state.sortDir = parsed.dir;
      applyFilters();
    });

    document.querySelectorAll(".sort-header").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.sort;
        if (state.sortKey === key) {
          state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        } else {
          state.sortKey = key;
          state.sortDir = "asc";
        }
        els.sortSelect.value =
          state.sortDir === "asc" && (key === "recordId" || key === "dudeneyGroup")
            ? key
            : `${key}-${state.sortDir}`;
        applyFilters();
      });
    });

    els.resetFilters.addEventListener("click", () => {
      els.searchInput.value = "";
      els.cohortSelect.value = "all";
      els.groupSelect.value = "all";
      els.magicOnly.checked = false;
      document.querySelectorAll('input[name="class-filter"]').forEach((i) => {
        i.checked = true;
      });
      els.sortSelect.value = "recordId";
      state.sortKey = "recordId";
      state.sortDir = "asc";
      applyFilters();
    });

    els.demoLoading.addEventListener("click", () => loadData({ simulateDelay: 900 }));
    els.demoError.addEventListener("click", () => loadData({ forceError: true }));
    els.reloadData.addEventListener("click", () => loadData());
  }

  wireEvents();
  loadData();
})();
