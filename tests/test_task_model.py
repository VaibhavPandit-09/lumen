from __future__ import annotations

import time
import unittest

from lumen.core.task import TaskInfo, TaskState


class TestTaskModel(unittest.TestCase):
    """Tests for lumen.core.task models."""

    def test_task_state_enum(self) -> None:
        expected_states = {
            "QUEUED": "QUEUED",
            "RUNNING": "RUNNING",
            "WAITING_FOR_AUTH": "WAITING_FOR_AUTH",
            "DOWNLOADING": "DOWNLOADING",
            "INSTALLING": "INSTALLING",
            "SUCCEEDED": "SUCCEEDED",
            "FAILED": "FAILED",
            "CANCELLED": "CANCELLED",
        }
        for name, value in expected_states.items():
            state = getattr(TaskState, name)
            self.assertEqual(state.value, value)

        all_states = {s.value for s in TaskState}
        self.assertEqual(all_states, set(expected_states.values()))

    def test_task_info_creation(self) -> None:
        before = time.time()
        task = TaskInfo(id="task-1", title="Installing Package")
        after = time.time()

        self.assertEqual(task.id, "task-1")
        self.assertEqual(task.title, "Installing Package")
        self.assertEqual(task.state, TaskState.QUEUED)
        self.assertEqual(task.progress_text, "")
        self.assertIsNone(task.result)
        self.assertEqual(task.error_message, "")
        self.assertTrue(before <= task.created_at <= after)
        self.assertTrue(before <= task.updated_at <= after)

    def test_task_info_state_update(self) -> None:
        task = TaskInfo(id="task-2", title="Updating System")
        initial_updated_at = task.updated_at

        time.sleep(0.01)
        task.update_state(TaskState.RUNNING, "Starting upgrade...")

        self.assertEqual(task.state, TaskState.RUNNING)
        self.assertEqual(task.progress_text, "Starting upgrade...")
        self.assertGreater(task.updated_at, initial_updated_at)

    def test_task_info_terminal_states(self) -> None:
        task = TaskInfo(id="task-3", title="Terminal Test")

        # Non-terminal states
        for non_term in (
            TaskState.QUEUED,
            TaskState.RUNNING,
            TaskState.WAITING_FOR_AUTH,
            TaskState.DOWNLOADING,
            TaskState.INSTALLING,
        ):
            task.state = non_term
            self.assertFalse(task.is_terminal(), f"{non_term} should not be terminal")

        # Terminal states
        for term in (TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED):
            task.state = term
            self.assertTrue(task.is_terminal(), f"{term} should be terminal")

    def test_task_info_to_dict(self) -> None:
        task = TaskInfo(
            id="task-4",
            title="Download Assets",
            state=TaskState.DOWNLOADING,
            progress_text="45%",
            result={"downloaded_bytes": 1048576},
            created_at=1000.0,
            updated_at=1010.0,
            error_message="",
        )

        expected = {
            "id": "task-4",
            "title": "Download Assets",
            "state": "DOWNLOADING",
            "progress_text": "45%",
            "result": {"downloaded_bytes": 1048576},
            "created_at": 1000.0,
            "updated_at": 1010.0,
            "error_message": "",
        }
        self.assertEqual(task.to_dict(), expected)


if __name__ == "__main__":
    unittest.main()
