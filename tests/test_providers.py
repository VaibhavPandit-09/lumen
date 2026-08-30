"""
Unit tests for system actions, locations, web search, and clipboard providers.
"""

import tempfile
import unittest
from pathlib import Path

from lumen.providers.calculator import CalculatorProvider
from lumen.providers.locations import LocationsProvider
from lumen.providers.recent_files import RecentFilesProvider
from lumen.providers.system_actions import SystemActionsProvider
from lumen.providers.web_search import WebSearchProvider


class TestProviders(unittest.TestCase):

    def test_system_actions_provider(self):
        prov = SystemActionsProvider()
        prov.initialize()

        res_lock = prov.search("lock")
        self.assertTrue(any(r.title == "Lock Screen" for r in res_lock))

        res_settings = prov.search("display")
        self.assertTrue(any("Display" in r.title for r in res_settings))

        res_reboot = prov.search("restart")
        self.assertTrue(any("Restart" in r.title for r in res_reboot))

    def test_locations_provider(self):
        prov = LocationsProvider()
        prov.initialize()

        res_home = prov.search("home")
        self.assertTrue(any(r.title == "Home" for r in res_home))

        res_down = prov.search("downloads")
        self.assertTrue(any(r.title == "Downloads" for r in res_down))

    def test_web_search_provider(self):
        prov = WebSearchProvider(engine_template="https://duckduckgo.com/?q=%s")
        res = prov.search("qt6 wayland protocol")
        self.assertEqual(len(res), 1)
        self.assertIn("qt6 wayland protocol", res[0].title)
        self.assertIn("https://duckduckgo.com/?q=qt6+wayland+protocol", res[0].context["url"])

    def test_calculator_provider(self):
        prov = CalculatorProvider()
        res = prov.search("50 * 4")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].title, "= 200")


if __name__ == "__main__":
    unittest.main()
