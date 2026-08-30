"""
Unit tests for the canonical ActionDispatcher execution engine.
"""

import time
import unittest

from lumen.core.actions.dispatcher import ActionDispatcher, DispatchResult, DispatchStatus
from lumen.core.models import ActionPayload, ActionType, SearchResult


class TestActionDispatcher(unittest.TestCase):
    """Tests synchronous and asynchronous action dispatching."""

    def test_sync_action_dispatch(self):
        called = []
        def _handler():
            called.append("executed")
            return 42

        item = SearchResult(
            id="test:sync",
            title="Sync Action",
            action=_handler,
        )

        res = ActionDispatcher.dispatch(item)
        self.assertEqual(res.status, DispatchStatus.SUCCESS)
        self.assertTrue(res.dismiss_window)
        self.assertEqual(called, ["executed"])
        self.assertEqual(res.output, 42)

    def test_confirmation_required_gate(self):
        called = []
        def _destructive():
            called.append("destroyed")

        item = SearchResult(
            id="test:destructive",
            title="Delete Database",
            requires_confirmation=True,
            confirm_prompt="Really delete?",
            action=_destructive,
        )

        # 1. Unconfirmed attempt
        res1 = ActionDispatcher.dispatch(item, confirmed=False)
        self.assertEqual(res1.status, DispatchStatus.CONFIRMATION_REQUIRED)
        self.assertFalse(res1.dismiss_window)
        self.assertEqual(res1.message, "Really delete?")
        self.assertEqual(called, [])

        # 2. Confirmed attempt
        res2 = ActionDispatcher.dispatch(item, confirmed=True)
        self.assertEqual(res2.status, DispatchStatus.SUCCESS)
        self.assertTrue(res2.dismiss_window)
        self.assertEqual(called, ["destroyed"])

    def test_async_action_dispatch(self):
        completed_results = []
        progress_messages = []

        def _slow_task():
            time.sleep(0.05)
            return "async_done"

        payload = ActionPayload(
            action_type=ActionType.PACKAGE_INSTALL,
            target="test-pkg",
            handler=_slow_task,
            is_async=True,
            success_message="Package installed!",
        )
        item = SearchResult(
            id="test:async",
            title="Install Slow Package",
            payload=payload,
        )

        def _on_progress(msg):
            progress_messages.append(msg)

        def _on_complete(res):
            completed_results.append(res)

        res = ActionDispatcher.dispatch(
            item=item,
            on_progress=_on_progress,
            on_complete=_on_complete,
        )

        self.assertEqual(res.status, DispatchStatus.RUNNING_ASYNC)
        self.assertFalse(res.dismiss_window)

        # Wait for thread completion
        time.sleep(0.15)
        self.assertEqual(len(completed_results), 1)
        self.assertEqual(completed_results[0].status, DispatchStatus.SUCCESS)
        self.assertEqual(completed_results[0].output, "async_done")

    def test_error_handling(self):
        def _failing_task():
            raise RuntimeError("Network disconnected")

        item = SearchResult(
            id="test:fail",
            title="Failing Action",
            action=_failing_task,
        )

        res = ActionDispatcher.dispatch(item)
        self.assertEqual(res.status, DispatchStatus.FAILED)
        self.assertFalse(res.dismiss_window)
        self.assertIn("Network disconnected", res.error_details)

    def test_sync_operation_result_failure(self):
        """When an action returns an object with success=False, dispatcher must report FAILED."""
        from lumen.core.packages.base import PackageOperationResult

        def _failed_op():
            return PackageOperationResult(success=False, message="Lock active", error_details="Locked")

        item = SearchResult(
            id="test:fail_op",
            title="Failed Operation",
            action=_failed_op,
        )

        res = ActionDispatcher.dispatch(item)
        self.assertEqual(res.status, DispatchStatus.FAILED)
        self.assertFalse(res.dismiss_window)
        self.assertEqual(res.message, "Lock active")
        self.assertEqual(res.error_details, "Locked")

    def test_async_operation_result_failure(self):
        """When an async action returns success=False, on_complete must receive FAILED status."""
        from lumen.core.packages.base import PackageOperationResult
        completed_results = []

        def _async_failed_op():
            return PackageOperationResult(success=False, message="APT error", error_details="Unmet deps")

        payload = ActionPayload(
            action_type=ActionType.PACKAGE_INSTALL,
            target="broken-pkg",
            handler=_async_failed_op,
            is_async=True,
            error_message="Custom error",
        )
        item = SearchResult(
            id="test:async_fail",
            title="Install Broken Package",
            payload=payload,
        )

        ActionDispatcher.dispatch(
            item=item,
            on_complete=lambda r: completed_results.append(r),
        )

        time.sleep(0.1)
        self.assertEqual(len(completed_results), 1)
        self.assertEqual(completed_results[0].status, DispatchStatus.FAILED)
        self.assertFalse(completed_results[0].dismiss_window)
        self.assertEqual(completed_results[0].message, "APT error")


if __name__ == "__main__":
    unittest.main()
