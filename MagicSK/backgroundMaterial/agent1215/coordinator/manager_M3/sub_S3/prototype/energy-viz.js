/**
 * Dependency-free SVG/HTML moment-energy visualization with table fallback.
 */
(function (global) {
  "use strict";

  const MODE_ORDER = [];
  for (let x = 0; x < 4; x += 1) {
    for (let y = 0; y < 4; y += 1) {
      if (x === 0 && y === 0) continue;
      MODE_ORDER.push(`M${x}${y}`);
    }
  }

  function energyColor(value, max) {
    const t = max > 0 ? Math.min(1, value / max) : 0;
    const r = Math.round(40 + t * 180);
    const g = Math.round(80 + (1 - t) * 60);
    const b = Math.round(180 - t * 80);
    return `rgb(${r}, ${g}, ${b})`;
  }

  function renderModeHeatmap(record) {
    const energies = MODE_ORDER.map((name) => record.modeEnergy[name] ?? 0);
    const max = Math.max(...energies, 1);
    const cellSize = 36;
    const pad = 28;
    const width = pad * 2 + cellSize * 4;
    const height = pad * 2 + cellSize * 4;

    const svgParts = [
      `<svg class="energy-svg" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="mode-heatmap-title" xmlns="http://www.w3.org/2000/svg">`,
      `<title id="mode-heatmap-title">Interaction mode energy heatmap for ${record.recordId}</title>`,
      `<desc>Grid of mode energies Mxy excluding M00. Darker blue indicates higher energy.</desc>`,
    ];

    for (let y = 0; y < 4; y += 1) {
      for (let x = 0; x < 4; x += 1) {
        const name = `M${x}${y}`;
        const px = pad + x * cellSize;
        const py = pad + y * cellSize;
        if (x === 0 && y === 0) {
          svgParts.push(
            `<rect x="${px}" y="${py}" width="${cellSize - 2}" height="${cellSize - 2}" fill="#30363d" stroke="#484f58" />`,
            `<text x="${px + cellSize / 2}" y="${py + cellSize / 2 + 4}" text-anchor="middle" fill="#7d8590" font-size="10">—</text>`
          );
          continue;
        }
        const value = record.modeEnergy[name] ?? 0;
        svgParts.push(
          `<rect x="${px}" y="${py}" width="${cellSize - 2}" height="${cellSize - 2}" fill="${energyColor(value, max)}" stroke="#484f58">`,
          `<title>${name}: ${value.toFixed(2)}</title></rect>`,
          `<text x="${px + cellSize / 2}" y="${py + cellSize / 2 + 4}" text-anchor="middle" fill="#0d1117" font-size="9" font-family="monospace">${name.slice(1)}</text>`
        );
      }
    }

    for (let i = 0; i <= 4; i += 1) {
      const pos = pad + i * cellSize;
      svgParts.push(`<line x1="${pos}" y1="${pad}" x2="${pos}" y2="${height - pad}" stroke="#484f58" stroke-width="0.5"/>`);
      svgParts.push(`<line x1="${pad}" y1="${pos}" x2="${width - pad}" y2="${pos}" stroke="#484f58" stroke-width="0.5"/>`);
    }

    svgParts.push("</svg>");
    return svgParts.join("");
  }

  function renderDegreeBars(record) {
    const degrees = ["2", "3", "4", "5", "6"];
    const values = degrees.map((d) => record.degreeEnergy[d] ?? 0);
    const max = Math.max(...values, 1);
    const barW = 28;
    const gap = 12;
    const chartW = degrees.length * (barW + gap) + 40;
    const chartH = 140;

    const parts = [
      `<svg class="energy-svg" viewBox="0 0 ${chartW} ${chartH}" role="img" aria-labelledby="degree-bar-title" xmlns="http://www.w3.org/2000/svg">`,
      `<title id="degree-bar-title">Degree energy bars for ${record.recordId}</title>`,
      `<desc>Bar heights show energy aggregated by total polynomial degree.</desc>`,
    ];

    degrees.forEach((degree, index) => {
      const value = values[index];
      const h = (value / max) * 90;
      const x = 30 + index * (barW + gap);
      const y = 110 - h;
      parts.push(
        `<rect x="${x}" y="${y}" width="${barW}" height="${h}" fill="${energyColor(value, max)}" stroke="#484f58">`,
        `<title>degree ${degree}: ${value.toFixed(2)}</title></rect>`,
        `<text x="${x + barW / 2}" y="125" text-anchor="middle" fill="#b1bac4" font-size="10">${degree}</text>`,
        `<text x="${x + barW / 2}" y="${y - 4}" text-anchor="middle" fill="#e6edf3" font-size="8">${value.toFixed(0)}</text>`
      );
    });

    parts.push("</svg>");
    return parts.join("");
  }

  function renderSummaryList(record) {
    const items = [
      ["Axial energy", record.axialEnergy],
      ["Interaction energy", record.interactionEnergy],
      ["Low-order energy", record.lowOrderEnergy],
      ["High-order energy", record.highOrderEnergy],
      ["Spectral centroid", record.spectralCentroid],
      ["Line defect energy", record.lineDefectEnergy],
    ];
    return `<ul class="energy-summary-list">${items
      .map(
        ([label, value]) =>
          `<li><span>${label}</span> <strong>${Number(value).toFixed(3)}</strong></li>`
      )
      .join("")}</ul>`;
  }

  function renderEnergyTable(record) {
    const modeRows = MODE_ORDER.map((name) => {
      const e = record.modeEnergy[name] ?? 0;
      const c = record.coefficients?.[name] ?? 0;
      return `<tr><th scope="row">${name}</th><td>${Number(c).toFixed(4)}</td><td>${Number(e).toFixed(2)}</td></tr>`;
    }).join("");

    const degreeRows = Object.entries(record.degreeEnergy || {})
      .sort((a, b) => Number(a[0]) - Number(b[0]))
      .map(
        ([deg, val]) =>
          `<tr><th scope="row">degree ${deg}</th><td>—</td><td>${Number(val).toFixed(2)}</td></tr>`
      )
      .join("");

    return `
      <table class="energy-table">
        <caption>Numeric moment coefficients and energies</caption>
        <thead><tr><th scope="col">Mode</th><th scope="col">Coefficient</th><th scope="col">Energy</th></tr></thead>
        <tbody>${modeRows}${degreeRows}</tbody>
      </table>`;
  }

  function render(container, record) {
    container.innerHTML = `
      <div class="energy-viz-wrap">
        <div class="energy-card">
          <h4>Mode energy heatmap (SVG)</h4>
          ${renderModeHeatmap(record)}
        </div>
        <div class="energy-card">
          <h4>Degree energy (SVG bars)</h4>
          ${renderDegreeBars(record)}
          ${renderSummaryList(record)}
        </div>
      </div>`;

    const alt = document.getElementById("energy-table-alt");
    if (alt) {
      alt.innerHTML = renderEnergyTable(record);
    }
  }

  global.EnergyViz = {
    render,
    renderEnergyTable,
    MODE_ORDER,
  };
})(window);
