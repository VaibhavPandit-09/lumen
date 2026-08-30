"""
Subtle, high-performance UI transitions and animations for Lumen.
"""

from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtCore import QEasingCurve, QObject, QParallelAnimationGroup, QPoint, QPropertyAnimation
from PyQt6.QtWidgets import QWidget


class WindowAnimationManager(QObject):
    """Manages smooth entry and dismissal transitions for the launcher window."""

    def __init__(self, window: QWidget, duration_ms: int = 120):
        super().__init__(window)
        self.window = window
        self.duration_ms = max(0, duration_ms)
        self._current_anim: Optional[QPropertyAnimation] = None

    def animate_show(self, on_finished: Optional[Callable[[], None]] = None) -> None:
        """Executes a subtle fade-in transition."""
        if self._current_anim and self._current_anim.state() == QPropertyAnimation.State.Running:
            self._current_anim.stop()

        if self.duration_ms <= 0:
            self.window.setWindowOpacity(1.0)
            self.window.show()
            if on_finished:
                on_finished()
            return

        self.window.setWindowOpacity(0.0)
        self.window.show()

        anim = QPropertyAnimation(self.window, b"windowOpacity", self)
        anim.setDuration(self.duration_ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        if on_finished:
            anim.finished.connect(on_finished)

        self._current_anim = anim
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def animate_hide(self, on_finished: Optional[Callable[[], None]] = None) -> None:
        """Executes a subtle fade-out transition before hiding the window."""
        if self._current_anim and self._current_anim.state() == QPropertyAnimation.State.Running:
            self._current_anim.stop()

        if self.duration_ms <= 0:
            self.window.hide()
            if on_finished:
                on_finished()
            return

        anim = QPropertyAnimation(self.window, b"windowOpacity", self)
        anim.setDuration(int(self.duration_ms * 0.8))  # Dismissal is slightly faster
        anim.setStartValue(self.window.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InQuad)

        def _cleanup():
            self.window.hide()
            self.window.setWindowOpacity(1.0)
            if on_finished:
                on_finished()

        anim.finished.connect(_cleanup)
        self._current_anim = anim
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
