"""
Unit tests for cached currency conversion provider.
"""

import unittest
from lumen.providers.currency import CurrencyProvider


class TestCurrency(unittest.TestCase):

    def setUp(self):
        self.provider = CurrencyProvider(enabled=True)
        # Fix mock baseline rates for testing
        self.provider.rates = {
            "EUR": 1.0,
            "USD": 1.10,
            "GBP": 0.85,
            "JPY": 160.0,
        }

    def test_parse_and_calculate_currency(self):
        # 110 USD to EUR -> should be 100 EUR
        results = self.provider.search("110 USD in EUR")
        self.assertEqual(len(results), 1)
        self.assertIn("100.00 EUR", results[0].title)

    def test_symbol_parsing(self):
        results = self.provider.search("$110 to EUR")
        self.assertEqual(len(results), 1)
        self.assertIn("100.00 EUR", results[0].title)

    def test_invalid_currency_query(self):
        self.assertEqual(self.provider.search("100 XYZ in ABC"), [])
        self.assertEqual(self.provider.search("random text"), [])


if __name__ == "__main__":
    unittest.main()
