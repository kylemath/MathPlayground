(function () {
  "use strict";

  const data = window.MAGIC_ANALYSIS;
  const helpers = window.MagicMoments;
  const PAGE_SIZE = 50;
  const COHORT_LABELS = {
    magic: "Magic",
    "swap-1": "1 pair swapped",
    "swap-2": "2 pairs swapped",
    "swap-3": "3 pairs swapped",
    random: "Random permutation",
  };
  const COHORT_ORDER = ["magic", "swap-1", "swap-2", "swap-3", "random"];

  const elements = {
    sourceCount: document.querySelector("#source-count"),
    orientedCount: document.querySelector("#oriented-count"),
    recordCount: document.querySelector("#record-count"),
    heightEnergy: document.querySelector("#height-energy"),
    cohortBody: document.querySelector("#cohort-body"),
    distributionMetric: document.querySelector("#distribution-metric"),
    distributionGroup: document.querySelector("#distribution-group"),
    distributionScale: document.querySelector("#distribution-scale"),
    distributionChart: document.querySelector("#distribution-chart"),
    distributionStatus: document.querySelector("#distribution-status"),
    resetDistribution: document.querySelector("#reset-distribution"),
    cohortFilter: document.querySelector("#cohort-filter"),
    groupFilter: document.querySelector("#group-filter"),
    classFilter: document.querySelector("#class-filter"),
    sortFilter: document.querySelector("#sort-filter"),
    searchFilter: document.querySelector("#search-filter"),
    resetFilters: document.querySelector("#reset-filters"),
    recordsBody: document.querySelector("#records-body"),
    resultStatus: document.querySelector("#result-status"),
    previousPage: document.querySelector("#previous-page"),
    nextPage: document.querySelector("#next-page"),
    pageStatus: document.querySelector("#page-status"),
    selectedTitle: document.querySelector("#selected-title"),
    magicBadge: document.querySelector("#magic-badge"),
    squareDiagram: document.querySelector("#square-diagram"),
    lineSums: document.querySelector("#line-sums"),
    selectedTags: document.querySelector("#selected-tags"),
    momentChart: document.querySelector("#moment-chart"),
    chartStatus: document.querySelector("#chart-status"),
    selectedMetrics: document.querySelector("#selected-metrics"),
    resetSelection: document.querySelector("#reset-selection"),
  };

  const state = {
    filtered: [],
    page: 1,
    selectedId: null,
  };

  function initializeSummary() {
    const metadata = data.metadata;
    elements.sourceCount.textContent = metadata.sourceCount.toLocaleString();
    elements.orientedCount.textContent =
      metadata.expandedOrientedCount.toLocaleString();
    elements.recordCount.textContent = data.records.length.toLocaleString();
    elements.heightEnergy.textContent = helpers.formatNumber(metadata.heightEnergy);

    const summaries = [...metadata.cohortSummary].sort(
      (left, right) =>
        COHORT_ORDER.indexOf(left.cohort) - COHORT_ORDER.indexOf(right.cohort),
    );
    elements.cohortBody.innerHTML = summaries
      .map(
        (summary) => `
          <tr>
            <td>${COHORT_LABELS[summary.cohort]}</td>
            <td>${summary.count.toLocaleString()}</td>
            <td>${summary.magicCount.toLocaleString()}</td>
            <td>${helpers.formatNumber(summary.meanLineDefect)}</td>
            <td>${helpers.formatNumber(summary.meanAxialEnergy)}</td>
            <td>${helpers.formatNumber(summary.meanLowOrderEnergy)}</td>
            <td>${helpers.formatNumber(summary.meanSpectralCentroid, 3)}</td>
          </tr>`,
      )
      .join("");

    Object.entries(metadata.groupLabels).forEach(([group, label]) => {
      const option = document.createElement("option");
      option.value = group;
      option.textContent = `${label} (${metadata.dudeneyCounts[group]})`;
      elements.groupFilter.append(option);
    });
  }

  function compareRecords(left, right, key) {
    const leftValue = left[key] ?? Number.POSITIVE_INFINITY;
    const rightValue = right[key] ?? Number.POSITIVE_INFINITY;
    if (leftValue === rightValue) {
      return left.recordId.localeCompare(right.recordId, undefined, { numeric: true });
    }
    return leftValue - rightValue;
  }

  function applyFilters({ resetPage = true } = {}) {
    const cohort = elements.cohortFilter.value;
    const group = elements.groupFilter.value;
    const structure = elements.classFilter.value;
    const query = elements.searchFilter.value.trim().toLowerCase();
    const sortKey = elements.sortFilter.value;

    state.filtered = data.records
      .filter((record) => cohort === "all" || record.cohort === cohort)
      .filter(
        (record) =>
          group === "all" || String(record.dudeneyGroup) === String(group),
      )
      .filter(
        (record) =>
          structure === "all" || record.classes.includes(structure),
      )
      .filter(
        (record) =>
          !query ||
          record.recordId.toLowerCase().includes(query) ||
          String(record.sourceId ?? "").includes(query),
      )
      .sort((left, right) => compareRecords(left, right, sortKey));

    if (resetPage) {
      state.page = 1;
    }
    const pageCount = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
    state.page = Math.min(state.page, pageCount);
    renderTable();
  }

  function renderTable() {
    const pageCount = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
    const start = (state.page - 1) * PAGE_SIZE;
    const pageRecords = state.filtered.slice(start, start + PAGE_SIZE);

    elements.resultStatus.textContent = `${state.filtered.length.toLocaleString()} records`;
    elements.pageStatus.textContent = `Page ${state.page} of ${pageCount}`;
    elements.previousPage.disabled = state.page <= 1;
    elements.nextPage.disabled = state.page >= pageCount;

    if (!pageRecords.length) {
      elements.recordsBody.innerHTML =
        '<tr><td colspan="12">No records match these filters.</td></tr>';
      return;
    }

    if (!pageRecords.some((record) => record.recordId === state.selectedId)) {
      state.selectedId = pageRecords[0].recordId;
    }

    elements.recordsBody.innerHTML = pageRecords
      .map(
        (record) => `
          <tr data-record-id="${record.recordId}"
              class="${record.recordId === state.selectedId ? "selected" : ""}"
              tabindex="0"
              aria-selected="${record.recordId === state.selectedId}">
            <td>${record.recordId}</td>
            <td>${COHORT_LABELS[record.cohort]}</td>
            <td>${record.dudeneyGroup ? `D${record.dudeneyGroup}` : "—"}</td>
            <td>${record.classes.join(", ")}</td>
            <td>${helpers.formatNumber(record.lineDefectEnergy)}</td>
            <td>${helpers.formatNumber(record.axialEnergy)}</td>
            <td>${helpers.formatNumber(record.degreeEnergy["2"])}</td>
            <td>${helpers.formatNumber(record.degreeEnergy["3"])}</td>
            <td>${helpers.formatNumber(record.degreeEnergy["4"])}</td>
            <td>${helpers.formatNumber(record.degreeEnergy["5"])}</td>
            <td>${helpers.formatNumber(record.degreeEnergy["6"])}</td>
            <td>${helpers.formatNumber(record.spectralCentroid, 3)}</td>
          </tr>`,
      )
      .join("");

    elements.recordsBody.querySelectorAll("tr[data-record-id]").forEach((row) => {
      row.addEventListener("click", () => selectRecord(row.dataset.recordId));
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectRecord(row.dataset.recordId);
        }
      });
    });

    const selected = data.records.find(
      (record) => record.recordId === state.selectedId,
    );
    if (selected) {
      renderDetail(selected);
    }
  }

  function selectRecord(recordId) {
    state.selectedId = recordId;
    const record = data.records.find((candidate) => candidate.recordId === recordId);
    if (!record) {
      return;
    }
    elements.recordsBody.querySelectorAll("tr").forEach((row) => {
      const selected = row.dataset.recordId === recordId;
      row.classList.toggle("selected", selected);
      row.setAttribute("aria-selected", String(selected));
    });
    renderDetail(record);
  }

  function renderDetail(record) {
    elements.selectedTitle.textContent = record.recordId;
    elements.magicBadge.textContent = record.isMagic ? "Magic" : "Imbalanced";
    elements.magicBadge.classList.toggle("not-magic", !record.isMagic);

    elements.squareDiagram.innerHTML = record.cells
      .map(
        (value) => `
          <div class="square-cell" style="--cell-color:${helpers.cellColor(value)}">
            ${value}<small>${value > 8.5 ? "+" : ""}${value - 8.5}</small>
          </div>`,
      )
      .join("");

    const sums = record.lineSums;
    elements.lineSums.innerHTML = `
      <div>Rows<strong>${sums.rows.join(" · ")}</strong></div>
      <div>Columns<strong>${sums.columns.join(" · ")}</strong></div>
      <div>Diagonals<strong>${sums.diagonals.join(" · ")}</strong></div>`;

    const tags = [
      ...record.classes,
      record.dudeneyLabel,
      record.selfComplementary ? "self-complementary" : null,
      `D4 orbit ${record.d4OrbitSize}`,
    ].filter(Boolean);
    elements.selectedTags.innerHTML = tags
      .map((tag) => `<span class="tag">${tag}</span>`)
      .join("");

    helpers.drawMomentChart(elements.momentChart, record);
    elements.chartStatus.textContent =
      `Mixed interaction energy ${helpers.formatNumber(record.interactionEnergy)} / ` +
      `${helpers.formatNumber(data.metadata.heightEnergy)}; low-order share ` +
      `${helpers.formatNumber((100 * record.lowOrderEnergy) / data.metadata.heightEnergy, 1)}%.`;

    const metrics = [
      ["Source index", record.sourceId ? `#${record.sourceId}` : "none"],
      ["Line-defect energy", helpers.formatNumber(record.lineDefectEnergy)],
      ["Axial energy", helpers.formatNumber(record.axialEnergy)],
      ["Interaction energy", helpers.formatNumber(record.interactionEnergy)],
      ["Low-order E₂ + E₃", helpers.formatNumber(record.lowOrderEnergy)],
      ["Higher E₄ + E₅ + E₆", helpers.formatNumber(record.highOrderEnergy)],
      ["Mean spectral degree", helpers.formatNumber(record.spectralCentroid, 4)],
      [
        "Complement partner",
        record.complementId ? `#${record.complementId}` : "not assigned",
      ],
    ];
    elements.selectedMetrics.innerHTML = metrics
      .map(([term, value]) => `<dt>${term}</dt><dd>${value}</dd>`)
      .join("");
  }

  function nestedValue(record, path) {
    return path.split(".").reduce((value, key) => value?.[key], record);
  }

  function distributionGroups(grouping, metric) {
    if (grouping === "dudeney") {
      const magic = data.records.filter((record) => record.cohort === "magic");
      return Array.from({ length: 12 }, (_, index) => {
        const group = index + 1;
        return {
          label: `D${group}`,
          values: magic
            .filter((record) => record.dudeneyGroup === group)
            .map((record) => nestedValue(record, metric)),
        };
      });
    }

    if (grouping === "structure") {
      const magic = data.records.filter((record) => record.cohort === "magic");
      const structures = [
        ["ordinary", "Ordinary"],
        ["associative", "Associative"],
        ["pandiagonal", "Pandiagonal"],
        ["most-perfect", "Most-perfect"],
      ];
      return structures.map(([key, label]) => ({
        label,
        values: magic
          .filter((record) => record.classes.includes(key))
          .map((record) => nestedValue(record, metric)),
      }));
    }

    return COHORT_ORDER.map((cohort) => ({
      label: COHORT_LABELS[cohort],
      values: data.records
        .filter((record) => record.cohort === cohort)
        .map((record) => nestedValue(record, metric)),
    }));
  }

  function renderDistribution() {
    const metric = elements.distributionMetric.value;
    const grouping = elements.distributionGroup.value;
    const scale = elements.distributionScale.value;
    const label =
      elements.distributionMetric.options[elements.distributionMetric.selectedIndex]
        .textContent;
    const groups = distributionGroups(grouping, metric);
    helpers.drawViolinChart(elements.distributionChart, groups, {
      label,
      scale,
    });

    const count = groups.reduce((sum, group) => sum + group.values.length, 0);
    const scope =
      grouping === "cohort"
        ? "all records"
        : "the 880 unperturbed magic squares";
    elements.distributionStatus.textContent =
      `${label} across ${groups.length} categories and ${count.toLocaleString()} values from ${scope}. ` +
      `Each violin is density-normalized within its category; axis is ${scale === "log" ? "log(1 + value)" : "linear"}.`;
  }

  function wireEvents() {
    [
      elements.cohortFilter,
      elements.groupFilter,
      elements.classFilter,
      elements.sortFilter,
    ].forEach((control) => {
      control.addEventListener("change", () => applyFilters());
    });
    elements.searchFilter.addEventListener("input", () => applyFilters());
    elements.resetFilters.addEventListener("click", () => {
      elements.cohortFilter.value = "magic";
      elements.groupFilter.value = "all";
      elements.classFilter.value = "all";
      elements.sortFilter.value = "sourceId";
      elements.searchFilter.value = "";
      applyFilters();
    });
    elements.previousPage.addEventListener("click", () => {
      state.page -= 1;
      renderTable();
    });
    elements.nextPage.addEventListener("click", () => {
      state.page += 1;
      renderTable();
    });
    elements.resetSelection.addEventListener("click", () => {
      if (state.filtered.length) {
        state.selectedId = state.filtered[0].recordId;
        state.page = 1;
        renderTable();
      }
    });
    [
      elements.distributionMetric,
      elements.distributionGroup,
      elements.distributionScale,
    ].forEach((control) => {
      control.addEventListener("change", renderDistribution);
    });
    elements.resetDistribution.addEventListener("click", () => {
      elements.distributionMetric.value = "lowOrderEnergy";
      elements.distributionGroup.value = "cohort";
      elements.distributionScale.value = "linear";
      renderDistribution();
    });
    window.addEventListener("resize", () => {
      const selected = data.records.find(
        (record) => record.recordId === state.selectedId,
      );
      if (selected) {
        helpers.drawMomentChart(elements.momentChart, selected);
      }
      renderDistribution();
    });
  }

  function initialize() {
    if (!data || !helpers) {
      elements.resultStatus.textContent = "Analysis data failed to load.";
      return;
    }
    initializeSummary();
    wireEvents();
    renderDistribution();
    applyFilters();
  }

  initialize();
})();
