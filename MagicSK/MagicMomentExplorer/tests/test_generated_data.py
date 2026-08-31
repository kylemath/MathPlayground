from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GeneratedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads((ROOT / "data" / "analysis.json").read_text())

    def test_record_and_cohort_counts(self) -> None:
        records = self.payload["records"]
        self.assertEqual(len(records), 4400)
        self.assertEqual(
            Counter(record["cohort"] for record in records),
            {
                "magic": 880,
                "swap-1": 880,
                "swap-2": 880,
                "swap-3": 880,
                "random": 880,
            },
        )

    def test_magic_partition_and_single_swap_damage(self) -> None:
        magic = [
            record for record in self.payload["records"] if record["cohort"] == "magic"
        ]
        swapped_once = [
            record
            for record in self.payload["records"]
            if record["cohort"] == "swap-1"
        ]
        self.assertTrue(all(record["axialEnergy"] == 0 for record in magic))
        self.assertTrue(
            all(abs(record["interactionEnergy"] - 340) < 1e-5 for record in magic)
        )
        self.assertTrue(all(not record["isMagic"] for record in swapped_once))

    def test_offline_browser_payload_exists(self) -> None:
        browser_payload = ROOT / "data" / "analysis-data.js"
        self.assertTrue(browser_payload.exists())
        self.assertGreater(browser_payload.stat().st_size, 1_000_000)


if __name__ == "__main__":
    unittest.main()
