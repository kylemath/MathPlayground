(function () {
  "use strict";

  const INTERACTION_MODES = [
    "M11",
    "M12",
    "M21",
    "M13",
    "M22",
    "M31",
    "M23",
    "M32",
    "M33",
  ];

  function formatNumber(value, digits = 2) {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return "—";
    }
    if (Math.abs(value) < 1e-9) {
      return "0";
    }
    return Number(value).toLocaleString(undefined, {
      maximumFractionDigits: digits,
    });
  }

  function cellColor(value) {
    const t = (value - 1) / 15;
    const hue = 215 - 175 * t;
    const lightness = 25 + 13 * t;
    return `hsl(${hue} 62% ${lightness}%)`;
  }

  function drawMomentChart(canvas, record) {
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(300, canvas.clientWidth);
    const height = Math.max(180, canvas.clientHeight);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);

    const context = canvas.getContext("2d");
    context.scale(ratio, ratio);
    context.clearRect(0, 0, width, height);

    const values = INTERACTION_MODES.map((name) => record.modeEnergy[name]);
    const maximum = Math.max(...values, 1);
    const padding = { top: 18, right: 8, bottom: 34, left: 40 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;
    const slot = plotWidth / values.length;
    const barWidth = Math.max(7, slot * 0.62);

    context.strokeStyle = "#30363d";
    context.fillStyle = "#7d8590";
    context.font = "10px -apple-system, BlinkMacSystemFont, sans-serif";
    context.textAlign = "right";
    context.textBaseline = "middle";

    for (let index = 0; index <= 4; index += 1) {
      const fraction = index / 4;
      const y = padding.top + plotHeight * (1 - fraction);
      context.beginPath();
      context.moveTo(padding.left, y);
      context.lineTo(width - padding.right, y);
      context.stroke();
      context.fillText(formatNumber(maximum * fraction, 0), padding.left - 6, y);
    }

    values.forEach((value, index) => {
      const barHeight = (value / maximum) * plotHeight;
      const x = padding.left + index * slot + (slot - barWidth) / 2;
      const y = padding.top + plotHeight - barHeight;
      const gradient = context.createLinearGradient(0, y, 0, padding.top + plotHeight);
      gradient.addColorStop(0, "#58a6ff");
      gradient.addColorStop(1, "#1f6feb");
      context.fillStyle = gradient;
      context.fillRect(x, y, barWidth, barHeight);

      context.fillStyle = "#b1bac4";
      context.textAlign = "center";
      context.textBaseline = "top";
      context.fillText(INTERACTION_MODES[index].slice(1), x + barWidth / 2, height - 24);
    });

    context.fillStyle = "#7d8590";
    context.textAlign = "left";
    context.textBaseline = "top";
    context.fillText("Energy", 0, 1);
  }

  function quantile(sortedValues, probability) {
    if (!sortedValues.length) {
      return 0;
    }
    const position = (sortedValues.length - 1) * probability;
    const lower = Math.floor(position);
    const remainder = position - lower;
    const upper = sortedValues[Math.min(lower + 1, sortedValues.length - 1)];
    return sortedValues[lower] + remainder * (upper - sortedValues[lower]);
  }

  function kernelDensity(values, samples, bandwidth) {
    const denominator = values.length * bandwidth * Math.sqrt(2 * Math.PI);
    return samples.map((sample) => {
      const total = values.reduce((sum, value) => {
        const distance = (sample - value) / bandwidth;
        return sum + Math.exp(-0.5 * distance * distance);
      }, 0);
      return total / denominator;
    });
  }

  function drawViolinChart(canvas, groups, options = {}) {
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(900, canvas.clientWidth);
    const height = Math.max(300, canvas.clientHeight);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);

    const context = canvas.getContext("2d");
    context.scale(ratio, ratio);
    context.clearRect(0, 0, width, height);

    const useLog = options.scale === "log";
    const transform = (value) => (useLog ? Math.log1p(Math.max(0, value)) : value);
    const invert = (value) => (useLog ? Math.expm1(value) : value);
    const prepared = groups
      .map((group) => ({
        ...group,
        rawValues: group.values.filter(Number.isFinite).sort((a, b) => a - b),
        values: group.values
          .filter(Number.isFinite)
          .map(transform)
          .sort((a, b) => a - b),
      }))
      .filter((group) => group.values.length);

    if (!prepared.length) {
      context.fillStyle = "#7d8590";
      context.font = "13px -apple-system, BlinkMacSystemFont, sans-serif";
      context.fillText("No values available for this grouping.", 24, 36);
      return;
    }

    const allValues = prepared.flatMap((group) => group.values);
    let minimum = Math.min(...allValues);
    let maximum = Math.max(...allValues);
    if (minimum === maximum) {
      const padding = Math.max(1, Math.abs(minimum) * 0.1);
      minimum = Math.max(0, minimum - padding);
      maximum += padding;
    } else {
      const padding = (maximum - minimum) * 0.04;
      minimum = Math.max(0, minimum - padding);
      maximum += padding;
    }

    const chartPadding = { top: 22, right: 20, bottom: 72, left: 68 };
    const plotWidth = width - chartPadding.left - chartPadding.right;
    const plotHeight = height - chartPadding.top - chartPadding.bottom;
    const slot = plotWidth / prepared.length;
    const maximumHalfWidth = Math.min(46, slot * 0.39);
    const sampleCount = 96;
    const samples = Array.from(
      { length: sampleCount },
      (_, index) => minimum + ((maximum - minimum) * index) / (sampleCount - 1),
    );
    const yFor = (value) =>
      chartPadding.top +
      plotHeight -
      ((value - minimum) / (maximum - minimum)) * plotHeight;

    context.font = "10px -apple-system, BlinkMacSystemFont, sans-serif";
    context.textAlign = "right";
    context.textBaseline = "middle";
    for (let index = 0; index <= 5; index += 1) {
      const fraction = index / 5;
      const value = minimum + (maximum - minimum) * fraction;
      const y = yFor(value);
      context.strokeStyle = "#30363d";
      context.lineWidth = 1;
      context.beginPath();
      context.moveTo(chartPadding.left, y);
      context.lineTo(width - chartPadding.right, y);
      context.stroke();
      context.fillStyle = "#7d8590";
      context.fillText(formatNumber(invert(value), 2), chartPadding.left - 8, y);
    }

    const colors = ["#58a6ff", "#3fb950", "#d29922", "#f85149", "#a371f7"];
    prepared.forEach((group, groupIndex) => {
      const centerX = chartPadding.left + slot * (groupIndex + 0.5);
      const range = group.values[group.values.length - 1] - group.values[0];
      const q1 = quantile(group.values, 0.25);
      const median = quantile(group.values, 0.5);
      const q3 = quantile(group.values, 0.75);
      const mean =
        group.values.reduce((sum, value) => sum + value, 0) / group.values.length;
      const standardDeviation = Math.sqrt(
        group.values.reduce((sum, value) => sum + (value - mean) ** 2, 0) /
          Math.max(1, group.values.length - 1),
      );
      const silverman =
        1.06 * standardDeviation * group.values.length ** (-1 / 5);
      const bandwidth = Math.max(
        silverman || 0,
        range / 30,
        (maximum - minimum) / 160,
        1e-6,
      );
      const densities = kernelDensity(group.values, samples, bandwidth);
      const peakDensity = Math.max(...densities, 1e-12);
      const widths = densities.map(
        (density) => (density / peakDensity) * maximumHalfWidth,
      );

      context.beginPath();
      samples.forEach((sample, index) => {
        const x = centerX - widths[index];
        const y = yFor(sample);
        if (index === 0) {
          context.moveTo(x, y);
        } else {
          context.lineTo(x, y);
        }
      });
      for (let index = samples.length - 1; index >= 0; index -= 1) {
        context.lineTo(centerX + widths[index], yFor(samples[index]));
      }
      context.closePath();
      context.fillStyle = `${colors[groupIndex % colors.length]}42`;
      context.strokeStyle = colors[groupIndex % colors.length];
      context.lineWidth = 1.4;
      context.fill();
      context.stroke();

      context.strokeStyle = "#e6edf3";
      context.lineWidth = 4;
      context.beginPath();
      context.moveTo(centerX, yFor(q1));
      context.lineTo(centerX, yFor(q3));
      context.stroke();
      context.fillStyle = "#e6edf3";
      context.beginPath();
      context.arc(centerX, yFor(median), 3.2, 0, Math.PI * 2);
      context.fill();

      context.save();
      context.translate(centerX, height - chartPadding.bottom + 15);
      if (prepared.length > 7) {
        context.rotate(-Math.PI / 5);
        context.textAlign = "right";
      } else {
        context.textAlign = "center";
      }
      context.textBaseline = "top";
      context.fillStyle = "#b1bac4";
      context.font = "11px -apple-system, BlinkMacSystemFont, sans-serif";
      context.fillText(group.label, 0, 0);
      context.restore();

      context.fillStyle = "#7d8590";
      context.textAlign = "center";
      context.textBaseline = "bottom";
      context.font = "9px -apple-system, BlinkMacSystemFont, sans-serif";
      context.fillText(`n=${group.rawValues.length}`, centerX, chartPadding.top - 5);
    });

    context.save();
    context.translate(14, chartPadding.top + plotHeight / 2);
    context.rotate(-Math.PI / 2);
    context.fillStyle = "#7d8590";
    context.font = "10px -apple-system, BlinkMacSystemFont, sans-serif";
    context.textAlign = "center";
    context.fillText(options.label || "Value", 0, 0);
    context.restore();
  }

  window.MagicMoments = {
    INTERACTION_MODES,
    cellColor,
    drawMomentChart,
    drawViolinChart,
    formatNumber,
  };
})();
