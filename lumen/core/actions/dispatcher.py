"""
Canonical action dispatch and execution pipeline for Lumen.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from lumen.core.logging import debug, error, info
from lumen.core.models import ActionType, SearchResult


class DispatchStatus(str, Enum):
    SUCCESS = "success"
    CONFIRMATION_REQUIRED = "confirmation_required"
    RUNNING_ASYNC = "running_async"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DispatchResult:
    status: DispatchStatus
    message: str = ""
    dismiss_window: bool = True
    error_details: Optional[str] = None
    output: Any = None


class ActionDispatcher:
    """Central execution authority for all search results and user actions."""

    @classmethod
    def dispatch(
        cls,
        item: SearchResult,
        on_progress: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[DispatchResult], None]] = None,
        confirmed: bool = False,
    ) -> DispatchResult:
        """
        Dispatches and executes the action for a given SearchResult.
        Guarantees identical behavior for keyboard (Enter) and mouse clicks.
        """
        if not item:
            return DispatchResult(status=DispatchStatus.FAILED, message="No item to execute", dismiss_window=False)

        # Check confirmation requirement
        if (item.requires_confirmation or (item.payload and item.payload.is_destructive)) and not confirmed:
            prompt = item.confirm_prompt or (item.payload.confirm_prompt if item.payload else "") or f"Confirm: {item.title}?"
            return DispatchResult(
                status=DispatchStatus.CONFIRMATION_REQUIRED,
                message=prompt,
                dismiss_window=False,
            )

        payload = item.payload
        is_async = payload.is_async if payload else False

        if is_async:
            def _async_worker():
                try:
                    if on_progress:
                        on_progress(f"Running {item.title}...")
                    out = item.execute()
                    
                    # Inspect operation result (e.g. PackageOperationResult or UpdateResult)
                    if hasattr(out, "success") and not out.success:
                        fail_msg = getattr(out, "message", "") or (payload.error_message if payload else "") or f"Failed: {item.title}"
                        err_det = getattr(out, "error_details", None)
                        res = DispatchResult(
                            status=DispatchStatus.FAILED,
                            message=fail_msg,
                            error_details=err_det,
                            dismiss_window=False,
                            output=out,
                        )
                    else:
                        succ_msg = (payload.success_message if payload else "") or (getattr(out, "message", "") if hasattr(out, "message") else "") or f"Completed: {item.title}"
                        res = DispatchResult(
                            status=DispatchStatus.SUCCESS,
                            message=succ_msg,
                            dismiss_window=True,
                            output=out,
                        )
                except Exception as e:
                    error("Dispatcher", f"Async action failed: {e}")
                    res = DispatchResult(
                        status=DispatchStatus.FAILED,
                        message=(payload.error_message if payload else "") or f"Failed: {item.title}",
                        error_details=str(e),
                        dismiss_window=False,
                    )
                if on_complete:
                    on_complete(res)

            t = threading.Thread(target=_async_worker, daemon=True)
            t.start()
            return DispatchResult(
                status=DispatchStatus.RUNNING_ASYNC,
                message=f"Started {item.title}...",
                dismiss_window=False,
            )

        # Synchronous execution
        try:
            out = item.execute()
            if hasattr(out, "success") and not out.success:
                fail_msg = getattr(out, "message", "") or f"Failed: {item.title}"
                err_det = getattr(out, "error_details", None)
                return DispatchResult(
                    status=DispatchStatus.FAILED,
                    message=fail_msg,
                    error_details=err_det,
                    dismiss_window=False,
                    output=out,
                )
            debug("Dispatcher", f"Executed action successfully: {item.title}")
            return DispatchResult(
                status=DispatchStatus.SUCCESS,
                message=f"Executed: {item.title}",
                dismiss_window=True,
                output=out,
            )
        except Exception as e:
            error("Dispatcher", f"Execution failed for {item.title}: {e}")
            return DispatchResult(
                status=DispatchStatus.FAILED,
                message=f"Could not execute: {item.title}",
                error_details=str(e),
                dismiss_window=False,
            )
