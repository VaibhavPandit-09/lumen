from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class TaskState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_FOR_AUTH = "WAITING_FOR_AUTH"
    DOWNLOADING = "DOWNLOADING"
    INSTALLING = "INSTALLING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class TaskInfo:
    id: str
    title: str
    state: TaskState = TaskState.QUEUED
    progress_text: str = ""
    result: Optional[Any] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    error_message: str = ""

    def is_terminal(self) -> bool:
        return self.state in (TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED)

    def update_state(self, state: TaskState, progress_text: str = "") -> None:
        self.state = state
        self.progress_text = progress_text
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "state": self.state.value,
            "progress_text": self.progress_text,
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message
        }
