"""
Unit tests for safe action execution and timeout handling.
"""

import sys
import unittest

from lumen.core.actions.executor import ActionContext, ActionExecutor
from lumen.core.actions.manifest import ActionDefinition


class TestActionsExecutor(unittest.TestCase):

    def test_build_argv_and_substitution(self):
        act = ActionDefinition(
            id="deploy",
            name="Deploy",
            exec=["echo", "Deploying", "to", "${target}"],
        )
        ctx = ActionContext(action_id="deploy", args={"target": "production"})
        argv = ActionExecutor.build_argv(act, ctx)
        self.assertEqual(argv, ["echo", "Deploying", "to", "production"])

    def test_successful_execution(self):
        act = ActionDefinition(
            id="py-hello",
            name="Hello",
            exec=[sys.executable, "-c", "print('Lumen Action OK')"],
        )
        res = ActionExecutor.execute(act)
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Lumen Action OK", res.stdout)

    def test_timeout_handling(self):
        act = ActionDefinition(
            id="sleep-long",
            name="Sleep",
            exec=[sys.executable, "-c", "import time; time.sleep(5)"],
            timeout_seconds=1,
        )
        res = ActionExecutor.execute(act, timeout=1)
        self.assertFalse(res.success)
        self.assertIn("timed out", res.error_message)

    def test_missing_executable(self):
        act = ActionDefinition(
            id="missing-bin",
            name="Missing",
            exec=["nonexistent_bin_123456789"],
        )
        res = ActionExecutor.execute(act)
        self.assertFalse(res.success)
        self.assertIn("not found", res.error_message)


if __name__ == "__main__":
    unittest.main()
