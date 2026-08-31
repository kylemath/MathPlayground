#!/usr/bin/env python3
"""Invariant checks for order-4 magic square enumeration and D4 canonicalization."""

from __future__ import annotations

import unittest

from d4 import (
    canonical,
    d4_orbit,
    d4_transforms,
    is_d4_canonical,
    orbit_size,
    stabilizer_size,
)
from enumerate import enumerate_oriented_magic_squares
from validate import MAGIC_CONSTANT, is_magic, is_normal, line_sums


class TestValidation(unittest.TestCase):
    def test_known_magic_square(self) -> None:
        grid = (
            1, 2, 15, 16,
            12, 14, 3, 5,
            13, 7, 10, 4,
            8, 11, 6, 9,
        )
        self.assertTrue(is_normal(grid))
        self.assertTrue(is_magic(grid))
        self.assertTrue(all(total == MAGIC_CONSTANT for total in line_sums(grid)))

    def test_non_magic_fails(self) -> None:
        grid = tuple(range(1, 17))
        self.assertTrue(is_normal(grid))
        self.assertFalse(is_magic(grid))


class TestD4(unittest.TestCase):
    def test_orbit_size_divides_eight(self) -> None:
        grid = (
            1, 2, 15, 16,
            12, 14, 3, 5,
            13, 7, 10, 4,
            8, 11, 6, 9,
        )
        self.assertEqual(len(d4_transforms(grid)), 8)
        self.assertEqual(orbit_size(grid), 8)
        self.assertEqual(stabilizer_size(grid), 1)

    def test_canonical_is_orbit_minimum(self) -> None:
        grid = (
            16, 15, 2, 1,
            5, 3, 14, 12,
            4, 10, 7, 13,
            9, 6, 11, 8,
        )
        canon = canonical(grid)
        self.assertEqual(canon, min(d4_orbit(grid)))
        self.assertTrue(is_d4_canonical(canon))

    def test_complement_excluded_from_d4_quotient(self) -> None:
        """Complement (17-x) is a value involution, not part of D4 canonicalization."""
        grid = (
            1, 2, 15, 16,
            12, 14, 3, 5,
            13, 7, 10, 4,
            8, 11, 6, 9,
        )
        complement = tuple(17 - value for value in grid)
        self.assertTrue(is_magic(complement))
        self.assertEqual(canonical(grid), min(d4_orbit(grid)))
        self.assertEqual(canonical(complement), min(d4_orbit(complement)))
        # D4 images permute positions only; complement relabels values in place.
        for image in d4_transforms(grid):
            self.assertEqual(sorted(image), sorted(grid))


class TestEnumeration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.oriented = enumerate_oriented_magic_squares()

    def test_oriented_count(self) -> None:
        self.assertEqual(len(self.oriented), 7040)

    def test_all_magic(self) -> None:
        self.assertTrue(all(is_magic(grid) for grid in self.oriented))

    def test_unique_oriented(self) -> None:
        self.assertEqual(len(set(self.oriented)), 7040)

    def test_canonical_count(self) -> None:
        canonical_set = {canonical(grid) for grid in self.oriented}
        self.assertEqual(len(canonical_set), 880)

    def test_all_canonical_orbits_size_eight(self) -> None:
        canonical_set = {canonical(grid) for grid in self.oriented}
        sizes = {orbit_size(grid) for grid in canonical_set}
        self.assertEqual(sizes, {8})

    def test_canonical_representatives_are_lex_min(self) -> None:
        canonical_set = {canonical(grid) for grid in self.oriented}
        for grid in canonical_set:
            self.assertEqual(grid, canonical(grid))


if __name__ == "__main__":
    unittest.main()
