"""
Unit tests for logging and privacy filters.
"""

import unittest
from lumen.core.logging import debug, error, info, is_debug, set_debug, warning


class TestLogging(unittest.TestCase):

    def test_debug_toggle(self):
        orig = is_debug()
        try:
            set_debug(True)
            self.assertTrue(is_debug())

            set_debug(False)
            self.assertFalse(is_debug())
        finally:
            set_debug(orig)

    def test_logging_calls_do_not_raise(self):
        set_debug(True)
        try:
            debug("TestTag", "Diagnostic message")
            info("TestTag", "Informational message")
            warning("TestTag", "Warning message")
            error("TestTag", "Error message", exc=ValueError("Sample error"))
        finally:
            set_debug(False)


if __name__ == "__main__":
    unittest.main()
