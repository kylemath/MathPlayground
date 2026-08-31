#!/usr/bin/env python3
"""Optional provenance spot-check: download Heinz pages and compare row counts."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "outputs" / "s1_provenance_fetch.json"

URLS = [
    "http://www.recmath.org/Magic%20Squares/order4lista.htm",
    "http://www.recmath.org/Magic%20Squares/order4listb.htm",
    "http://www.recmath.org/Magic%20Squares/order4listc.htm",
    "http://www.recmath.org/Magic%20Squares/order4listd.htm",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def parse_records(text: str) -> int:
    count = 0
    for line in text.splitlines():
        values = [int(v) for v in re.findall(r"\d+", line)]
        if len(values) == 21 and 1 <= values[0] <= 880:
            cells = values[3:19]
            if sorted(cells) == list(range(1, 17)):
                count += 1
    return count


def main() -> int:
    per_page: dict[str, int] = {}
    total = 0
    errors: list[str] = []
    for url in URLS:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "S1-verify/1.0 (read-only audit)"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            text = TextExtractor()
            text.feed(raw.decode("windows-1252", errors="replace"))
            n = parse_records(text.text())
            per_page[url] = n
            total += n
        except Exception as exc:  # noqa: BLE001 — audit script
            errors.append(f"{url}: {exc}")

    result = {
        "pages_fetched": len(per_page),
        "records_per_page": per_page,
        "total_parsed_records": total,
        "expected": 880,
        "matches_expected": total == 880,
        "errors": errors,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if total == 880 and not errors else 1


if __name__ == "__main__":
    sys.exit(main())
