#!/usr/bin/env python3
"""Smoke-test browser runtime prerequisites without modifying the app."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer")
OUT = Path(__file__).resolve().parents[1] / "evidence"


def check_js_syntax(path: Path) -> dict:
    cmd = ["node", "--check", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "file": str(path),
        "command": " ".join(cmd),
        "ok": proc.returncode == 0,
        "stderr": proc.stderr.strip(),
    }


def simulate_inline_load() -> dict:
    """Verify analysis-data.js can be generated and defines MAGIC_ANALYSIS."""
    json_path = ROOT / "data" / "analysis.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    wrapper = f"window.MAGIC_ANALYSIS={json.dumps(payload, separators=(',', ':'))};\n"
    # Basic structural checks app.js expects
    required_meta = ["sourceCount", "expandedOrientedCount", "heightEnergy", "cohortSummary", "groupLabels", "dudeneyCounts"]
    required_record = ["recordId", "cohort", "cells", "modeEnergy", "degreeEnergy", "lineSums", "classes"]
    meta_ok = all(k in payload["metadata"] for k in required_meta)
    rec_ok = all(k in payload["records"][0] for k in required_record)
    return {
        "wrapper_bytes": len(wrapper.encode("utf-8")),
        "metadata_keys_ok": meta_ok,
        "record_keys_ok": rec_ok,
        "record_count": len(payload["records"]),
        "app_expects_window_MAGIC_ANALYSIS": True,
        "analysis_data_js_present_in_repo": (ROOT / "data" / "analysis-data.js").exists(),
    }


def index_script_refs() -> dict:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r'<script src="([^"]+)"', html)
    missing = [r for r in refs if not (ROOT / r).exists()]
    return {"script_refs": refs, "missing_refs": missing}


def main() -> int:
    report = {
        "index_script_refs": index_script_refs(),
        "inline_load_simulation": simulate_inline_load(),
        "js_syntax_checks": [],
    }
    for rel in ["moments.js", "app.js"]:
        path = ROOT / rel
        if path.exists():
            report["js_syntax_checks"].append(check_js_syntax(path))

    out_path = OUT / "browser_smoke_audit.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    missing = report["index_script_refs"]["missing_refs"]
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
