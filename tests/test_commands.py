"""
Unit tests for CommandProvider and nested submenus.
"""

import unittest
from lumen.core.models import CommandItem
from lumen.providers.commands import CommandProvider


class TestCommandsProvider(unittest.TestCase):

    def setUp(self):
        self.commands = [
            CommandItem(
                name="Docker Submenu",
                description="Manage Docker",
                subcommands=[
                    CommandItem(name="Docker Up", command="docker compose up -d", description="Start containers"),
                    CommandItem(name="Docker Down", command="docker compose down", description="Stop containers"),
                ],
            ),
            CommandItem(
                name="Single Command",
                command="echo single",
                description="Run single command",
                keywords=["single", "test"],
            ),
        ]
        self.provider = CommandProvider(commands=self.commands)
        self.provider.initialize()

    def test_direct_search_nested_items(self):
        # Direct global query should find both top-level and nested commands
        results_up = self.provider.search("Docker Up")
        self.assertTrue(any(r.title == "Docker Up" for r in results_up))

        results_single = self.provider.search("Single")
        self.assertTrue(any(r.title == "Single Command" for r in results_single))

    def test_top_level_subcommands_structure(self):
        top_results = self.provider._cached_results
        self.assertEqual(len(top_results), 2)

        docker_menu = next(r for r in top_results if r.title == "Docker Submenu")
        self.assertTrue(docker_menu.has_subcommands())
        self.assertEqual(len(docker_menu.subcommands), 2)
        self.assertEqual(docker_menu.subcommands[0].title, "Docker Up")


if __name__ == "__main__":
    unittest.main()
