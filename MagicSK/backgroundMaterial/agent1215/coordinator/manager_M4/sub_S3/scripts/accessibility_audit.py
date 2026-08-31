#!/usr/bin/env python3
"""Static HTML/CSS accessibility checklist for app vs M3 prototype."""

from __future__ import annotations

import json
import re
from pathlib import Path

APP_HTML = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/index.html")
APP_CSS = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/styles.css")
M3_HTML = Path(
    "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/"
    "coordinator/manager_M3/sub_S3/prototype/index.html"
)
M3_CSS = Path(
    "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/"
    "coordinator/manager_M3/sub_S3/prototype/styles.css"
)
OUT = Path(__file__).resolve().parents[1] / "evidence"


def scan_html(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return {
        "path": str(path),
        "lang_en": 'lang="en"' in text,
        "viewport": "viewport" in text,
        "skip_link": "skip-link" in text or "Skip to" in text,
        "main_landmark": bool(re.search(r"<main\b", text)),
        "aria_labels": len(re.findall(r"aria-[a-z]+=", text)),
        "role_attrs": len(re.findall(r'\brole="', text)),
        "status_live_regions": len(re.findall(r'role="status"|aria-live=', text)),
        "table_caption": "<caption" in text,
        "canvas_charts": len(re.findall(r"<canvas\b", text)),
        "labeled_form_controls": len(re.findall(r"<label\b", text)),
        "fieldset_legend": "<fieldset" in text,
        "button_types": len(re.findall(r'<button[^>]*type="button"', text)),
        "h1_count": len(re.findall(r"<h1\b", text)),
    }


def scan_css(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return {
        "path": str(path),
        "prefers_reduced_motion": "prefers-reduced-motion" in text,
        "focus_visible": ":focus-visible" in text or ":focus" in text,
        "color_scheme_dark": "color-scheme" in text,
        "min_touch_target_40px": "min-height: 40px" in text or "min-height:40px" in text,
        "visually_hidden": "visually-hidden" in text or "sr-only" in text,
    }


def contrast_estimate(css_text: str) -> dict:
    """Rough token presence for contrast auditing (not computed WCAG ratios)."""
    pairs = {
        "text_on_bg": ("--text", "--bg"),
        "text_primary_on_panel": ("--text-primary", "--bg-panel"),
        "secondary_text": ("--text-secondary", "--bg-deep"),
    }
    found = {name: all(tok in css_text for tok in tokens) for name, tokens in pairs.items()}
    return {
        "css_variables_present": found,
        "note": "M3 uses explicit --text-primary/#e6edf3 on #0d1117; app uses --text/--bg — likely AA for body text but chart/canvas needs text fallback",
    }


def main() -> int:
    app_html = scan_html(APP_HTML)
    m3_html = scan_html(M3_HTML)
    app_css = scan_css(APP_CSS)
    m3_css = scan_css(M3_CSS)

    gaps = []
    checks = [
        ("skip_link", app_html["skip_link"], m3_html["skip_link"]),
        ("prefers_reduced_motion", app_css["prefers_reduced_motion"], m3_css["prefers_reduced_motion"]),
        ("table_caption", app_html["table_caption"], m3_html["table_caption"]),
        ("fieldset_legend", app_html["fieldset_legend"], m3_html["fieldset_legend"]),
    ]
    for name, app_val, m3_val in checks:
        if m3_val and not app_val:
            gaps.append(f"app_missing:{name} (present in M3 prototype)")

    report = {
        "app_html_scan": app_html,
        "m3_html_scan": m3_html,
        "app_css_scan": app_css,
        "m3_css_scan": m3_css,
        "contrast_estimate": contrast_estimate(APP_CSS.read_text(encoding="utf-8")),
        "gaps_vs_m3_prototype": gaps,
        "recommendations": [
            "Add skip-to-main link and prefers-reduced-motion CSS block (M3 pattern).",
            "Replace canvas-only chart with SVG or provide hidden data table + aria-describedby (M3 energy-viz pattern).",
            "Implement square diagram as role=grid with keyboard roving tabindex (M3 diagram.js).",
            "Add <caption> to data tables; associate filters with aria-controls where live-updating.",
            "Ensure chart-status and result-status announce filter/pagination changes (aria-live=polite).",
            "Provide text alternative for line sums (M3 line-sums-table).",
            "Verify 4.5:1 contrast for --muted/#7d8590 on --panel backgrounds.",
        ],
    }

    out_path = OUT / "accessibility_audit.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
