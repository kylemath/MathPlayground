#!/usr/bin/env python3
"""Download and normalize Harvey Heinz's 880 Frénicle order-4 squares."""

from __future__ import annotations

import argparse
import csv
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SOURCE_PAGES = [
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


def download_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MagicMomentExplorer/1.0 (reproducible research)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
    parser = TextExtractor()
    parser.feed(raw.decode("windows-1252", errors="replace"))
    return parser.text()


def parse_records(text: str) -> list[dict[str, int]]:
    records: list[dict[str, int]] = []
    for line in text.splitlines():
        values = [int(value) for value in re.findall(r"\d+", line)]
        if len(values) != 21 or not 1 <= values[0] <= 880:
            continue
        square_id, group, orientation, *tail = values
        cells, pair_number, complement_id = tail[:16], tail[16], tail[17]
        if sorted(cells) != list(range(1, 17)):
            continue
        record = {
            "id": square_id,
            "dudeney_group": group,
            "group_orientation": orientation,
            **{f"cell_{index + 1}": value for index, value in enumerate(cells)},
            "complement_pair": pair_number,
            "complement_id": complement_id,
        }
        records.append(record)
    return records


def validate(records: list[dict[str, int]]) -> None:
    ids = [record["id"] for record in records]
    if ids != list(range(1, 881)):
        missing = sorted(set(range(1, 881)) - set(ids))
        raise ValueError(
            f"Expected IDs 1..880 in order; got {len(ids)} records. "
            f"First missing IDs: {missing[:10]}"
        )

    for record in records:
        cells = [record[f"cell_{index}"] for index in range(1, 17)]
        rows = [sum(cells[offset : offset + 4]) for offset in range(0, 16, 4)]
        columns = [sum(cells[column::4]) for column in range(4)]
        diagonals = [
            sum(cells[index * 5] for index in range(4)),
            sum(cells[3 + index * 3] for index in range(4)),
        ]
        if rows + columns + diagonals != [34] * 10:
            raise ValueError(f"Source record {record['id']} is not magic")


def write_csv(records: list[dict[str, int]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "dudeney_group",
        "group_orientation",
        *[f"cell_{index}" for index in range(1, 17)],
        "complement_pair",
        "complement_id",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "magic_squares_880.csv",
    )
    args = parser.parse_args()

    records: list[dict[str, int]] = []
    for url in SOURCE_PAGES:
        records.extend(parse_records(download_text(url)))
    records.sort(key=lambda record: record["id"])
    validate(records)
    write_csv(records, args.output)
    print(f"Wrote {len(records)} validated squares to {args.output}")


if __name__ == "__main__":
    main()
