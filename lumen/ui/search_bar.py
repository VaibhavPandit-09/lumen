"""
Custom search bar widget with keyboard navigation hooks.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLineEdit


class SearchBar(QLineEdit):
    """Search input field forwarding navigation and shortcut keys."""

    navigate_signal = pyqtSignal(int)      # Up / Down / PageUp / PageDown
    activate_signal = pyqtSignal()         # Enter / Return
    dismiss_signal = pyqtSignal()          # Escape
    drill_down_signal = pyqtSignal()       # Tab / Right Arrow
    pop_level_signal = pyqtSignal()        # Backspace on empty text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LumenSearchBar")
        self.setPlaceholderText("Search applications, commands, files, or calculate...")
        self.setClearButtonEnabled(True)

    def keyPressEvent(self, event):
        key = event.key()

        # Handle navigation keys
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            self.navigate_signal.emit(key)
            event.accept()
            return

        # Handle activation
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.activate_signal.emit()
            event.accept()
            return

        # Handle dismiss
        if key == Qt.Key.Key_Escape:
            self.dismiss_signal.emit()
            event.accept()
            return

        # Handle drill down into submenu
        if key == Qt.Key.Key_Tab or (key == Qt.Key.Key_Right and self.cursorPosition() == len(self.text())):
            self.drill_down_signal.emit()
            event.accept()
            return

        # Handle backspace on empty text to go up one menu level
        if key == Qt.Key.Key_Backspace and not self.text():
            self.pop_level_signal.emit()
            event.accept()
            return

        super().keyPressEvent(event)
