#!/usr/bin/env bash
# S1 verification runner — captures stdout to outputs/
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$DIR/outputs"
mkdir -p "$OUT"

echo "=== s1_independent_verify.py ===" | tee "$OUT/run_log.txt"
python3 "$DIR/scripts/s1_independent_verify.py" 2>&1 | tee "$OUT/s1_independent_verify_stdout.txt"

echo "" | tee -a "$OUT/run_log.txt"
echo "=== s1_analysis_cohort_check.py ===" | tee -a "$OUT/run_log.txt"
python3 "$DIR/scripts/s1_analysis_cohort_check.py" 2>&1 | tee "$OUT/s1_analysis_cohort_check_stdout.txt"

echo "" | tee -a "$OUT/run_log.txt"
echo "=== head magic_squares_880.csv ===" | tee -a "$OUT/run_log.txt"
head -n 3 /Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv | tee "$OUT/source_csv_head.txt"

echo "" | tee -a "$OUT/run_log.txt"
echo "=== wc source files ===" | tee -a "$OUT/run_log.txt"
wc -l /Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv \
       /Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.csv | tee "$OUT/wc_lines.txt"

echo "Done." | tee -a "$OUT/run_log.txt"
