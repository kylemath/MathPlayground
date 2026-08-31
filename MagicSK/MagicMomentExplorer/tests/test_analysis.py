from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze  # noqa: E402


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = analyze.load_source(ROOT / "data" / "magic_squares_880.csv")

    def test_reference_census(self) -> None:
        self.assertEqual(len(self.records), 880)
        self.assertTrue(all(analyze.is_magic(record["cells"]) for record in self.records))
        self.assertEqual(
            len({analyze.canonical(record["cells"]) for record in self.records}),
            880,
        )

    def test_dudeney_group_counts(self) -> None:
        expected = {
            1: 48,
            2: 48,
            3: 48,
            4: 96,
            5: 96,
            6: 304,
            7: 56,
            8: 56,
            9: 56,
            10: 56,
            11: 8,
            12: 8,
        }
        self.assertEqual(
            Counter(record["dudeney_group"] for record in self.records),
            expected,
        )

    def test_basis_is_orthonormal(self) -> None:
        for left_index, left in enumerate(analyze.BASIS):
            for right_index, right in enumerate(analyze.BASIS):
                target = 1.0 if left_index == right_index else 0.0
                self.assertAlmostEqual(analyze.dot(left, right), target, places=12)

    def test_parseval_energy_partition(self) -> None:
        examples = [
            self.records[0]["cells"],
            self.records[479]["cells"],
            list(range(1, 17)),
        ]
        for cells in examples:
            metrics = analyze.moment_metrics(cells)
            total = metrics["axialEnergy"] + metrics["interactionEnergy"]
            self.assertAlmostEqual(total, analyze.TOTAL_HEIGHT_ENERGY, places=5)

    def test_magic_eliminates_all_axial_modes(self) -> None:
        for record in self.records:
            metrics = analyze.moment_metrics(record["cells"])
            self.assertAlmostEqual(metrics["axialEnergy"], 0.0, places=7)
            self.assertAlmostEqual(
                metrics["interactionEnergy"],
                analyze.TOTAL_HEIGHT_ENERGY,
                places=5,
            )

    def test_known_structural_counts(self) -> None:
        pandiagonal = sum(
            analyze.is_pandiagonal(record["cells"]) for record in self.records
        )
        associative = sum(
            analyze.is_associative(record["cells"]) for record in self.records
        )
        most_perfect = sum(
            analyze.is_most_perfect(record["cells"]) for record in self.records
        )
        self.assertEqual(pandiagonal, 48)
        self.assertEqual(associative, 48)
        self.assertEqual(most_perfect, 48)


if __name__ == "__main__":
    unittest.main()
