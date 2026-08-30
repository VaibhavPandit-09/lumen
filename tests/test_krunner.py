"""
Unit tests for KRunner provider adapter.
"""

import unittest
from lumen.providers.krunner import KRunnerProvider


class TestKRunnerProvider(unittest.TestCase):

    def test_offline_graceful_degradation(self):
        prov = KRunnerProvider(enabled=True)
        prov.initialize()

        # Offline/headless should not raise exceptions
        results = prov.safe_search("system")
        self.assertIsInstance(results, list)

    def test_disabled_provider_returns_empty(self):
        prov = KRunnerProvider(enabled=False)
        self.assertEqual(prov.safe_search("anything"), [])


if __name__ == "__main__":
    unittest.main()
