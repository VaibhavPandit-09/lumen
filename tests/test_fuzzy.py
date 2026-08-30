"""
Unit tests for fuzzy matching and acronym recognition engine.
"""

import unittest
from lumen.core.fuzzy import fuzzy_match, get_acronym, score_item


class TestFuzzyMatching(unittest.TestCase):

    def test_exact_match(self):
        matched, score = fuzzy_match("firefox", "Firefox")
        self.assertTrue(matched)
        self.assertGreaterEqual(score, 1000.0)

    def test_prefix_match(self):
        matched, score = fuzzy_match("fire", "Firefox")
        self.assertTrue(matched)
        self.assertGreater(score, 800.0)

    def test_acronym_match(self):
        # KSystemLog -> ksl or ksp
        self.assertEqual(get_acronym("Google Chrome"), "gc")
        self.assertEqual(get_acronym("Visual Studio Code"), "vsc")
        self.assertEqual(get_acronym("KSystemLog"), "ksl")

        matched, score = fuzzy_match("gc", "Google Chrome")
        self.assertTrue(matched)
        self.assertGreaterEqual(score, 550.0)

        matched_vsc, score_vsc = fuzzy_match("vsc", "Visual Studio Code")
        self.assertTrue(matched_vsc)

    def test_word_boundary_match(self):
        matched, score = fuzzy_match("term", "Ghostty Terminal")
        self.assertTrue(matched)
        self.assertGreater(score, 500.0)

    def test_fuzzy_subsequence(self):
        matched, score = fuzzy_match("ffox", "Firefox")
        self.assertTrue(matched)
        self.assertGreater(score, 0.0)

    def test_non_matching(self):
        matched, score = fuzzy_match("xyz", "Firefox")
        self.assertFalse(matched)
        self.assertEqual(score, 0.0)

    def test_score_item_weights(self):
        # Title match should score higher than subtitle match
        _, title_score = score_item("docker", "Docker Desktop", "Container manager")
        _, sub_score = score_item("docker", "Podman", "Alternative to Docker")
        self.assertGreater(title_score, sub_score)

    def test_empty_query(self):
        matched, score = score_item("", "Any Application")
        self.assertTrue(matched)
        self.assertEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
