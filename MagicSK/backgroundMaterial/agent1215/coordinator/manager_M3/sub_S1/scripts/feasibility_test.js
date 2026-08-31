#!/usr/bin/env node
/**
 * Zero-dependency payload/performance feasibility harness.
 * Run: node scripts/feasibility_test.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { performance } = require('perf_hooks');
const { gunzipSync } = require('zlib');

const ROOT = path.resolve(__dirname, '..');
const JSON_PATH = path.join(ROOT, 'data', 'magic_moment_v1_880.json');
const GZ_PATH = JSON_PATH + '.gz';
const EXAMPLE_PATH = path.join(ROOT, 'data', 'magic_moment_v1_example.json');
const FULL_ANALYSIS = '/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.json';

const CLASS_FLAGS = {
  pandiagonal: 1,
  associative: 2,
  'most-perfect': 4,
  ordinary: 8,
};

function decodeFlags(flags) {
  return Object.entries(CLASS_FLAGS)
    .filter(([, bit]) => (flags & bit) !== 0)
    .map(([label]) => label);
}

const SHA256_RE = /^[a-f0-9]{64}$/;

function validateProvenance(meta) {
  const errors = [];
  if (!meta || meta.schemaVersion !== '1.0.0') {
    errors.push('meta.schemaVersion must be 1.0.0');
  }
  const provenance = meta?.provenance;
  if (!provenance?.sourceSha256 || !SHA256_RE.test(provenance.sourceSha256)) {
    errors.push('meta.provenance.sourceSha256 must be a 64-char lowercase hex digest');
  }
  if (provenance?.checksumPolicy !== 'sha256-of-source-csv-at-build') {
    errors.push('meta.provenance.checksumPolicy must be sha256-of-source-csv-at-build');
  }
  return errors;
}

function validateV1(bundle, { requireFullRecordCount = true } = {}) {
  const errors = validateProvenance(bundle.meta);
  const { records } = bundle;
  if (requireFullRecordCount) {
    if (!Array.isArray(records) || records.length !== 880) {
      errors.push(`records length expected 880, got ${records?.length}`);
    }
  } else if (!Array.isArray(records) || records.length < 1) {
    errors.push('records must be a non-empty array');
  }
  const seen = new Set();
  for (const row of records || []) {
    const id = row[0];
    if (id < 1 || id > 880) errors.push(`id out of range: ${id}`);
    if (seen.has(id)) errors.push(`duplicate id: ${id}`);
    seen.add(id);
    const cells = row[1];
    if (!Array.isArray(cells) || cells.length !== 16) errors.push(`bad cells for id ${id}`);
    const sorted = [...cells].sort((a, b) => a - b).join(',');
    if (sorted !== '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16') {
      errors.push(`cells not a permutation for id ${id}`);
    }
    if (!Array.isArray(row[7]) || row[7].length !== 15) errors.push(`bad coefficients for id ${id}`);
    if (!Array.isArray(row[8]) || row[8].length !== 5) errors.push(`bad energy summary for id ${id}`);
  }
  return errors;
}

function normalizeV1(bundle) {
  const fields = bundle.meta.recordLayout.fields;
  return bundle.records.map((tuple) => {
    const obj = {};
    fields.forEach((key, index) => {
      obj[key] = tuple[index];
    });
    obj.classLabels = decodeFlags(obj.classFlags);
    return obj;
  });
}

function filterSortRender(records) {
  const filtered = records.filter(
    (r) => r.dudeneyGroup === 6 && (r.classFlags & CLASS_FLAGS.ordinary) !== 0
  );
  filtered.sort((a, b) => b.energySummary[3] - a.energySummary[3]);
  const top = filtered.slice(0, 10).map((r) => ({
    id: r.id,
    highOrder: r.energySummary[3],
    cells: r.cells,
  }));
  return { filteredCount: filtered.length, top };
}

function bench(label, fn) {
  const t0 = performance.now();
  const result = fn();
  const ms = performance.now() - t0;
  return { label, ms: Number(ms.toFixed(3)), result };
}

function main() {
  const report = {
    timestamp: new Date().toISOString(),
    environment: { node: process.version, platform: process.platform },
    files: {},
    timings: [],
    validation: {},
    strategy: {},
    comparisons: {},
  };

  for (const filePath of [JSON_PATH, GZ_PATH, EXAMPLE_PATH]) {
    if (fs.existsSync(filePath)) {
      report.files[path.basename(filePath)] = fs.statSync(filePath).size;
    }
  }

  const raw = fs.readFileSync(JSON_PATH, 'utf8');
  const parseBench = bench('json.parse(880 records)', () => JSON.parse(raw));
  const bundle = parseBench.result;
  report.timings.push({ phase: parseBench.label, ms: parseBench.ms });

  const errors = validateV1(bundle);
  report.validation.errorCount = errors.length;
  report.validation.sampleErrors = errors.slice(0, 5);
  report.validation.sourceSha256 = bundle.meta?.provenance?.sourceSha256 || null;

  const normBench = bench('normalize tuples -> objects', () => normalizeV1(bundle));
  report.timings.push({ phase: normBench.label, ms: normBench.ms });

  const uiBench = bench('filter+sort+top10 render prep', () => filterSortRender(normBench.result));
  report.timings.push({ phase: uiBench.label, ms: uiBench.ms, filteredCount: uiBench.result.filteredCount });

  if (fs.existsSync(GZ_PATH)) {
    const gzBench = bench('gunzip + parse', () => {
      const inflated = gunzipSync(fs.readFileSync(GZ_PATH));
      return JSON.parse(inflated.toString('utf8'));
    });
    report.timings.push({ phase: gzBench.label, ms: gzBench.ms });
    report.files.compressionRatio = Number((report.files['magic_moment_v1_880.json'] / report.files['magic_moment_v1_880.json.gz']).toFixed(2));
  }

  if (fs.existsSync(FULL_ANALYSIS)) {
    const fullSize = fs.statSync(FULL_ANALYSIS).size;
    report.comparisons.fullAnalysisJsonBytes = fullSize;
    report.comparisons.compactReductionFactor = Number((fullSize / report.files['magic_moment_v1_880.json']).toFixed(2));
  }

  if (fs.existsSync(EXAMPLE_PATH)) {
    const example = JSON.parse(fs.readFileSync(EXAMPLE_PATH, 'utf8'));
    const exampleErrors = validateV1(example, { requireFullRecordCount: false });
    report.validation.exampleErrorCount = exampleErrors.length;
    report.validation.exampleSourceSha256 = example.meta?.provenance?.sourceSha256 || null;
    report.validation.exampleMatchesFull =
      report.validation.exampleSourceSha256 === report.validation.sourceSha256;
  }

  report.strategy = {
    parsing: 'Single JSON.parse on load; lazy normalize per view if needed.',
    rendering: 'Keep tuple form in memory; materialize objects on filter/sort only.',
    browserConstraints: '152 KB raw fits main-thread parse <50 ms on modern hardware; gzip ~32 KB for HTTP.',
    localFileVsHttp: 'file:// works with fetch-free XHR/FileReader; HTTP enables gzip Content-Encoding.',
    stableIds: 'Use tuple[0] as primary key; never array index.',
    migration: 'Gate on meta.schemaVersion; reject unknown versions with user-facing error state.',
  };

  const outPath = path.join(ROOT, 'data', 'feasibility_report.json');
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main();
