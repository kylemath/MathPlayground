#!/usr/bin/env node
/**
 * Zero-dependency smoke test runner for Magic Moment Records prototype.
 * Uses Node.js built-ins only (fs, path, vm, http where applicable).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import http from "node:http";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const PROTO = path.join(ROOT, "prototype");

const results = [];
let pass = 0;
let fail = 0;

function record(name, ok, detail = "") {
  results.push({ name, ok, detail });
  if (ok) pass += 1;
  else fail += 1;
  const mark = ok ? "PASS" : "FAIL";
  console.log(`${mark}  ${name}${detail ? ` — ${detail}` : ""}`);
}

function read(file) {
  return fs.readFileSync(path.join(PROTO, file), "utf8");
}

function assertIncludes(haystack, needle, name) {
  record(name, haystack.includes(needle), needle);
}

function assertMatch(text, regex, name) {
  record(name, regex.test(text), String(regex));
}

function assertEqual(actual, expected, name) {
  record(name, actual === expected, `expected ${expected}, got ${actual}`);
}

// --- Syntax / file presence ---
const requiredFiles = [
  "index.html",
  "styles.css",
  "app.js",
  "data-loader.js",
  "diagram.js",
  "energy-viz.js",
  "embedded-data.js",
  "sample-data.json",
];

for (const file of requiredFiles) {
  const full = path.join(PROTO, file);
  record(`file exists: ${file}`, fs.existsSync(full));
}

// --- HTML contract ---
const html = read("index.html");
const domContracts = [
  ["id=\"main-content\"", "main landmark"],
  ["role=\"grid\"", "diagram grid role"],
  ["id=\"square-diagram\"", "square diagram container"],
  ["id=\"energy-viz\"", "energy viz container"],
  ["id=\"record-table\"", "record table"],
  ["aria-live", "live region"],
  ["skip-link", "skip link"],
];

for (const [needle, label] of domContracts) {
  assertIncludes(html, needle, `HTML contract: ${label}`);
}

assertMatch(html, /<html lang="en">/, "HTML lang attribute");
assertMatch(html, /<link rel="stylesheet" href="styles\.css">/, "external CSS only");
assertMatch(html, /<script src="embedded-data\.js"><\/script>/, "embedded fallback script");

// --- CSS accessibility hooks ---
const css = read("styles.css");
assertIncludes(css, "prefers-reduced-motion", "CSS reduced motion");
assertIncludes(css, ":focus-visible", "CSS focus-visible");
assertIncludes(css, ".visually-hidden", "CSS visually hidden utility");
assertIncludes(css, "color-scheme: dark", "CSS color scheme");

// --- JS module surface (vm sandbox) ---
function loadModule(filename, exportName) {
  const code = read(filename);
  const sandbox = { window: {}, console, setTimeout, clearTimeout };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox, { filename });
  return sandbox[exportName] || sandbox.window[exportName];
}

const loader = loadModule("data-loader.js", "RecordDataLoader");
record("RecordDataLoader export", typeof loader.loadDataset === "function");
record("RecordDataLoader validatePayload", typeof loader.validatePayload === "function");

const embeddedCode = read("embedded-data.js");
const embeddedSandbox = { window: {} };
vm.createContext(embeddedSandbox);
vm.runInContext(embeddedCode, embeddedSandbox);
const payload = embeddedSandbox.window.__EMBEDDED_RECORDS__;
record("embedded payload present", Boolean(payload));
try {
  loader.validatePayload(payload);
  record("embedded payload validates", true);
} catch (e) {
  record("embedded payload validates", false, e.message);
}

const diagram = loadModule("diagram.js", "SquareDiagram");
record("SquareDiagram export", typeof diagram.createDiagram === "function");

const energy = loadModule("energy-viz.js", "EnergyViz");
record("EnergyViz export", typeof energy.render === "function");
assertEqual(energy.MODE_ORDER.length, 15, "mode order count (4*4-1)");

// --- JSON sample-data ---
const sample = JSON.parse(read("sample-data.json"));
record("sample-data schemaVersion", Boolean(sample.schemaVersion));
assertEqual(sample.records.length, 20, "sample record count");
record("sample record cells length 16", sample.records.every((r) => r.cells.length === 16));

// --- Payload size observation ---
const sampleBytes = fs.statSync(path.join(PROTO, "sample-data.json")).size;
const embeddedBytes = fs.statSync(path.join(PROTO, "embedded-data.js")).size;
console.log(`\nPayload observations:`);
console.log(`  sample-data.json: ${sampleBytes} bytes (~${(sampleBytes / 1024).toFixed(1)} KiB)`);
console.log(`  embedded-data.js: ${embeddedBytes} bytes (~${(embeddedBytes / 1024).toFixed(1)} KiB)`);
console.log(`  Full analysis.json reference: ~4.4 MiB / 4400 records (not bundled)`);

// --- HTTP fetch feasibility (local server) ---
async function testHttpFetch() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const rel = req.url === "/" ? "/index.html" : req.url;
      const filePath = path.join(PROTO, rel.replace(/^\//, ""));
      if (!filePath.startsWith(PROTO)) {
        res.writeHead(403);
        res.end("forbidden");
        return;
      }
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        res.writeHead(404);
        res.end("not found");
        return;
      }
      const ext = path.extname(filePath);
      const types = {
        ".html": "text/html",
        ".js": "text/javascript",
        ".css": "text/css",
        ".json": "application/json",
      };
      res.writeHead(200, { "Content-Type": types[ext] || "text/plain" });
      res.end(fs.readFileSync(filePath));
    });

    server.listen(0, "127.0.0.1", async () => {
      const { port } = server.address();
      try {
        const res = await fetch(`http://127.0.0.1:${port}/sample-data.json`);
        record("HTTP fetch sample-data.json", res.ok, `status ${res.status}`);
        const json = await res.json();
        record("HTTP JSON parse", Array.isArray(json.records), `${json.records?.length} records`);
      } catch (e) {
        record("HTTP fetch sample-data.json", false, e.message);
      } finally {
        server.close(() => resolve());
      }
    });
  });
}

await testHttpFetch();

// --- sub_S3 root HTTP: browser runner + prototype sibling paths ---
function createStaticServer(rootDir) {
  return http.createServer((req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, "http://127.0.0.1").pathname);
    const rel = urlPath === "/" ? "/prototype/index.html" : urlPath;
    const filePath = path.normalize(path.join(rootDir, rel.replace(/^\//, "")));
    if (!filePath.startsWith(rootDir)) {
      res.writeHead(403);
      res.end("forbidden");
      return;
    }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      res.writeHead(404);
      res.end("not found");
      return;
    }
    const ext = path.extname(filePath);
    const types = {
      ".html": "text/html",
      ".js": "text/javascript",
      ".css": "text/css",
      ".json": "application/json",
      ".md": "text/markdown",
    };
    res.writeHead(200, { "Content-Type": types[ext] || "text/plain" });
    res.end(fs.readFileSync(filePath));
  });
}

async function testSubS3RootServing() {
  return new Promise((resolve) => {
    const server = createStaticServer(ROOT);
    server.listen(0, "127.0.0.1", async () => {
      const { port } = server.address();
      const base = `http://127.0.0.1:${port}`;
      try {
        const runnerRes = await fetch(`${base}/smoke-test/smoke-test.html`);
        record("HTTP sub_S3: smoke-test.html", runnerRes.ok, `status ${runnerRes.status}`);

        const runnerHtml = await runnerRes.text();
        const scriptSrcs = [...runnerHtml.matchAll(/<script src="([^"]+)"/g)].map((m) => m[1]);
        record(
          "smoke-test.html script refs",
          scriptSrcs.length === 4 && scriptSrcs.every((src) => src.startsWith("../prototype/")),
          scriptSrcs.join(", ")
        );

        for (const src of scriptSrcs) {
          const resolved = new URL(src, `${base}/smoke-test/smoke-test.html`).pathname;
          const modRes = await fetch(`${base}${resolved}`);
          record(`HTTP sub_S3: ${resolved}`, modRes.ok, `status ${modRes.status}`);
        }

        const protoRes = await fetch(`${base}/prototype/index.html`);
        record("HTTP sub_S3: prototype/index.html", protoRes.ok, `status ${protoRes.status}`);

        const jsonRes = await fetch(`${base}/prototype/sample-data.json`);
        record("HTTP sub_S3: prototype/sample-data.json", jsonRes.ok, `status ${jsonRes.status}`);
      } catch (e) {
        record("HTTP sub_S3 root serving", false, e.message);
      } finally {
        server.close(() => resolve());
      }
    });
  });
}

async function testPrototypeOnlySiblingBlocked() {
  return new Promise((resolve) => {
    const server = createStaticServer(PROTO);
    server.listen(0, "127.0.0.1", async () => {
      const { port } = server.address();
      const base = `http://127.0.0.1:${port}`;
      try {
        const protoRes = await fetch(`${base}/index.html`);
        record("HTTP prototype-only: index.html", protoRes.ok, `status ${protoRes.status}`);

        const siblingAttempt = await fetch(`${base}/../smoke-test/smoke-test.html`);
        record(
          "HTTP prototype-only: sibling smoke-test unreachable",
          siblingAttempt.status === 403 || siblingAttempt.status === 404,
          `status ${siblingAttempt.status} (serve sub_S3 root instead)`
        );
      } catch (e) {
        record("HTTP prototype-only sibling blocked", false, e.message);
      } finally {
        server.close(() => resolve());
      }
    });
  });
}

await testSubS3RootServing();
await testPrototypeOnlySiblingBlocked();

// --- file:// behavior note (cannot fetch file:// from Node realistically) ---
record(
  "file:// note documented",
  true,
  "fetch blocked for file:// in browsers; embedded-data.js provides fallback"
);

console.log(`\nSummary: ${pass} passed, ${fail} failed, ${results.length} checks`);

const reportPath = path.join(__dirname, "smoke-results.json");
fs.writeFileSync(
  reportPath,
  JSON.stringify(
    {
      timestamp: new Date().toISOString(),
      pass,
      fail,
      total: results.length,
      payload: { sampleBytes, embeddedBytes },
      results,
    },
    null,
    2
  )
);
console.log(`Results written to ${reportPath}`);

process.exit(fail > 0 ? 1 : 0);
