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
        self.setPlaceholderText("Type a command, application, calculation, or search...")
        self.setClearButtonEnabled(True)
        self.setAccessibleName("Lumen Search Query Input")
        self.setAccessibleDescription("Type search query, math calculation, or command name")

    def keyPressEvent(self, event):
        key = event.key()

        # Handle navigation keys (Up, Down, PageUp, PageDown)
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            self.navigate_signal.emit(key)
            event.accept()
            return

        # Handle activation (Enter, Return)
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.activate_signal.emit()
            event.accept()
            return

        # Handle dismiss (Escape)
        if key == Qt.Key.Key_Escape:
            self.dismiss_signal.emit()
            event.accept()
            return

        # Handle drill down into submenu (Tab, Right Arrow at end of text)
        if key == Qt.Key.Key_Tab and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.drill_down_signal.emit()
            event.accept()
            return

        if key == Qt.Key.Key_Right and self.cursorPosition() == len(self.text()):
            self.drill_down_signal.emit()
            event.accept()
            return

        # Handle Shift+Tab or Left Arrow at start of text / Backspace on empty to go back
        if (key == Qt.Key.Key_Tab and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)) or \
           (key == Qt.Key.Key_Left and self.cursorPosition() == 0 and not self.text()) or \
           (key == Qt.Key.Key_Backspace and not self.text()):
            self.pop_level_signal.emit()
            event.accept()
            return

        super().keyPressEvent(event)
