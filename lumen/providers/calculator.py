"""
Calculator search provider supporting instant math and percentage calculations.
"""

from __future__ import annotations

import subprocess
from typing import List

from lumen.core.calculator import evaluate_expression
from lumen.core.models import ItemCategory, SearchResult
from lumen.providers.base import BaseProvider

try:
    from PyQt6.QtWidgets import QApplication
    HAS_QT_APP = True
except ImportError:
    HAS_QT_APP = False


def copy_to_clipboard(text: str) -> None:
    """Copies text to the system clipboard."""
    if HAS_QT_APP:
        app = QApplication.instance()
        if app:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
                return

    # Fallback to wl-copy or xclip / xsel if Qt clipboard not ready
    for tool, args in [("wl-copy", [text]), ("xclip", ["-selection", "clipboard"]), ("xsel", ["-b", "-i"])]:
        import shutil
        if shutil.which(tool):
            try:
                p = subprocess.Popen([tool] + (args if tool == "wl-copy" else []), stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                return
            except Exception:
                continue


class CalculatorProvider(BaseProvider):
    """Evaluates mathematical expressions typed in search bar and copies result on activation."""

    def __init__(self, enabled: bool = True):
        super().__init__("calculator", enabled=enabled)

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled or not query:
            return []

        calc_res = evaluate_expression(query)
        if not calc_res:
            return []

        result_text = calc_res.result_str
        return [
            SearchResult(
                id=f"calc:{calc_res.expression}",
                title=f"= {result_text}",
                subtitle=f"Calculation: {calc_res.expression} (Press Enter to copy)",
                category=ItemCategory.CALCULATION.value,
                icon_name="accessories-calculator",
                score=1000.0,  # Highest priority when math expression is typed
                action=lambda val=result_text: copy_to_clipboard(val),
                badge="Calc",
                keywords=["calc", "math", "evaluate"],
                context={"result": result_text, "expression": calc_res.expression},
            )
        ]
