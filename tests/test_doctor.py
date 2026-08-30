"""
Unit tests for SystemDoctor health check diagnostics and reporting.
"""

import unittest
from lumen.core.doctor import CheckStatus, DoctorReport, SystemDoctor


class TestDoctor(unittest.TestCase):

    def test_run_all_checks(self):
        report = SystemDoctor.run_all_checks()
        self.assertIsInstance(report, DoctorReport)
        self.assertGreater(len(report.checks), 8)

        # Python and PyQt6 checks must pass in test environment
        py_check = next((c for c in report.checks if c.name == "Python Runtime"), None)
        self.assertIsNotNone(py_check)
        self.assertEqual(py_check.status, CheckStatus.PASS)

        pyqt_check = next((c for c in report.checks if c.name == "PyQt6 Bindings"), None)
        self.assertIsNotNone(pyqt_check)
        self.assertEqual(pyqt_check.status, CheckStatus.PASS)

    def test_report_serialization(self):
        report = SystemDoctor.run_all_checks()
        d = report.to_dict()

        self.assertIn("version", d)
        self.assertIn("healthy", d)
        self.assertIn("has_warnings", d)
        self.assertIn("checks", d)
        self.assertIsInstance(d["checks"], list)
        self.assertGreater(len(d["checks"]), 0)

        # Check fields of each diagnostic check
        for c in d["checks"]:
            self.assertIn("name", c)
            self.assertIn("status", c)
            self.assertIn("message", c)
            self.assertIn("details", c)
            self.assertIn("fix_suggestion", c)

    def test_formatted_text_output(self):
        report = SystemDoctor.run_all_checks()
        text = report.format_text()

        self.assertIn("Lumen Doctor Diagnostic Report", text)
        self.assertIn("Python Runtime", text)
        self.assertIn("PyQt6 Bindings", text)


if __name__ == "__main__":
    unittest.main()
