/**
 * Data loader with embedded fallback for file:// and fetch for HTTP serving.
 * Schema version 0.1.0-prototype
 */
(function (global) {
  "use strict";

  const EMBEDDED_SAMPLE = null; // populated after first fetch attempt fails on file://

  /**
   * @returns {Promise<{schemaVersion:string, metadata:object, records:object[]}>}
   */
  async function loadDataset(options = {}) {
    const delay = options.simulateDelay ?? 0;
    if (delay > 0) {
      await new Promise((resolve) => setTimeout(resolve, delay));
    }

    if (options.forceError) {
      throw new Error("Simulated dataset load failure (demo error state).");
    }

    const candidates = [
      "sample-data.json",
      "./sample-data.json",
    ];

    let lastError = null;
    for (const url of candidates) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} for ${url}`);
        }
        const payload = await response.json();
        validatePayload(payload);
        return payload;
      } catch (error) {
        lastError = error;
      }
    }

    if (global.__EMBEDDED_RECORDS__) {
      validatePayload(global.__EMBEDDED_RECORDS__);
      return global.__EMBEDDED_RECORDS__;
    }

    throw lastError || new Error("Unable to load dataset from fetch or embedded fallback.");
  }

  function validatePayload(payload) {
    if (!payload || typeof payload !== "object") {
      throw new Error("Dataset payload is not an object.");
    }
    if (!payload.schemaVersion) {
      throw new Error("Missing schemaVersion.");
    }
    if (!Array.isArray(payload.records)) {
      throw new Error("Missing records array.");
    }
    if (payload.records.length === 0) {
      throw new Error("Records array is empty.");
    }
    const sample = payload.records[0];
    const required = ["recordId", "cells", "modeEnergy", "degreeEnergy", "interactionEnergy"];
    for (const key of required) {
      if (!(key in sample)) {
        throw new Error(`Record missing required field: ${key}`);
      }
    }
    if (!Array.isArray(sample.cells) || sample.cells.length !== 16) {
      throw new Error("Record cells must be length 16.");
    }
  }

  function describeServeMode() {
    const protocol = global.location?.protocol || "unknown:";
    if (protocol === "file:") {
      return {
        mode: "file",
        note: "fetch(sample-data.json) may fail under file://; embedded fallback used when present.",
      };
    }
    if (protocol === "http:" || protocol === "https:") {
      return {
        mode: "http",
        note: "fetch(sample-data.json) should succeed when served from prototype directory.",
      };
    }
    return { mode: protocol, note: "Unknown protocol." };
  }

  global.RecordDataLoader = {
    loadDataset,
    validatePayload,
    describeServeMode,
  };
})(window);
