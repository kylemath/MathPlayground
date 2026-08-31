#!/usr/bin/env bash
# Run all S2 audit scripts and capture stdout. Standard library only; no venv required.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p outputs evidence

echo "=== S2 audit run $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee outputs/run_all.log

for script in basis_parseval_audit control_repro_audit full_record_scan control_cells_match evidence_table; do
  echo "--- scripts/${script}.py ---" | tee -a outputs/run_all.log
  python3 "scripts/${script}.py" 2>&1 | tee -a "outputs/${script}.txt"
done

echo "=== All audits complete ===" | tee -a outputs/run_all.log
