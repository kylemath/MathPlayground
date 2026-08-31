/**
 * Keyboard-operable 4×4 square diagram.
 */
(function (global) {
  "use strict";

  const N = 4;

  function cellsToMatrix(cells) {
    const matrix = [];
    for (let row = 0; row < N; row += 1) {
      matrix.push(cells.slice(row * N, (row + 1) * N));
    }
    return matrix;
  }

  function createDiagram(container, record, callbacks = {}) {
    container.innerHTML = "";
    const matrix = cellsToMatrix(record.cells);
    const cells = [];
    let focusedIndex = 0;
    let selectedIndex = null;

    matrix.forEach((rowValues, row) => {
      rowValues.forEach((value, col) => {
        const index = row * N + col;
        const button = document.createElement("button");
        button.type = "button";
        button.className = "square-cell";
        button.setAttribute("role", "gridcell");
        button.dataset.row = String(row);
        button.dataset.col = String(col);
        button.dataset.index = String(index);
        button.textContent = String(value);
        button.setAttribute("aria-label", `Row ${row + 1}, column ${col + 1}, value ${value}`);
        button.tabIndex = index === 0 ? 0 : -1;

        button.addEventListener("click", () => {
          selectCell(index);
          focusCell(index, false);
        });

        button.addEventListener("focus", () => {
          focusedIndex = index;
          updateHighlights();
          announceCell(index);
        });

        container.appendChild(button);
        cells.push(button);
      });
    });

    container.addEventListener("keydown", (event) => {
      const row = Math.floor(focusedIndex / N);
      const col = focusedIndex % N;
      let nextRow = row;
      let nextCol = col;

      switch (event.key) {
        case "ArrowUp":
          nextRow = Math.max(0, row - 1);
          event.preventDefault();
          break;
        case "ArrowDown":
          nextRow = Math.min(N - 1, row + 1);
          event.preventDefault();
          break;
        case "ArrowLeft":
          nextCol = Math.max(0, col - 1);
          event.preventDefault();
          break;
        case "ArrowRight":
          nextCol = Math.min(N - 1, col + 1);
          event.preventDefault();
          break;
        case "Home":
          nextCol = 0;
          event.preventDefault();
          break;
        case "End":
          nextCol = N - 1;
          event.preventDefault();
          break;
        case "Enter":
        case " ":
          event.preventDefault();
          selectCell(focusedIndex);
          return;
        case "Escape":
          selectedIndex = null;
          updateHighlights();
          announceCell(focusedIndex);
          return;
        default:
          return;
      }

      focusCell(nextRow * N + nextCol, true);
    });

    function focusCell(index, moveFocus) {
      focusedIndex = index;
      cells.forEach((cell, i) => {
        cell.tabIndex = i === index ? 0 : -1;
      });
      if (moveFocus) {
        cells[index].focus();
      }
      updateHighlights();
      announceCell(index);
    }

    function selectCell(index) {
      selectedIndex = selectedIndex === index ? null : index;
      updateHighlights();
      announceCell(index);
      if (typeof callbacks.onSelect === "function") {
        callbacks.onSelect(index, record.cells[index], selectedIndex);
      }
    }

    function updateHighlights() {
      const selRow = selectedIndex === null ? null : Math.floor(selectedIndex / N);
      const selCol = selectedIndex === null ? null : selectedIndex % N;
      const focRow = Math.floor(focusedIndex / N);
      const focCol = focusedIndex % N;

      cells.forEach((cell, index) => {
        const row = Math.floor(index / N);
        const col = index % N;
        cell.classList.toggle("is-selected", index === selectedIndex);
        const highlight =
          (selRow !== null && row === selRow) ||
          (selCol !== null && col === selCol) ||
          (selectedIndex === null && (row === focRow || col === focCol));
        cell.classList.toggle("is-row-col-highlight", highlight);
      });
    }

    function announceCell(index) {
      const row = Math.floor(index / N);
      const col = index % N;
      const value = record.cells[index];
      const status = document.getElementById("diagram-status");
      if (!status) return;
      const selectedText =
        selectedIndex === index ? " Selected." : selectedIndex === null ? "" : "";
      status.textContent = `Cell R${row + 1}C${col + 1} = ${value}.${selectedText}`;
    }

    updateHighlights();
    return {
      focusFirst: () => focusCell(0, true),
      getSelectedIndex: () => selectedIndex,
    };
  }

  function renderLineSumsTable(table, record) {
    const tbody = table.querySelector("tbody");
    tbody.innerHTML = "";
    const sums = record.lineSums || {};
    const rows = [
      ["Rows", (sums.rows || []).join(", "), record.lineDefectEnergy],
      ["Columns", (sums.columns || []).join(", "), "—"],
      ["Diagonals", (sums.diagonals || []).join(", "), "—"],
    ];
    rows.forEach(([kind, values, defect]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<th scope="row">${kind}</th><td>${values}</td><td>${defect}</td>`;
      tbody.appendChild(tr);
    });
  }

  global.SquareDiagram = {
    createDiagram,
    renderLineSumsTable,
    cellsToMatrix,
  };
})(window);
