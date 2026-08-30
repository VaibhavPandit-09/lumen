"""
Unit tests for safe calculator and percentage evaluation.
"""

import unittest
from lumen.core.calculator import evaluate_expression, preprocess_expression


class TestCalculator(unittest.TestCase):

    def test_basic_arithmetic(self):
        res1 = evaluate_expression("2 + 2")
        self.assertIsNotNone(res1)
        self.assertEqual(res1.result_str, "4")

        res2 = evaluate_expression("15 * 27")
        self.assertIsNotNone(res2)
        self.assertEqual(res2.result_str, "405")

        res3 = evaluate_expression("100 / 4")
        self.assertIsNotNone(res3)
        self.assertEqual(res3.result_str, "25")

        res4 = evaluate_expression("2 ** 8")
        self.assertIsNotNone(res4)
        self.assertEqual(res4.result_str, "256")

        res5 = evaluate_expression("2 ^ 8")
        self.assertIsNotNone(res5)
        self.assertEqual(res5.result_str, "256")

    def test_math_functions(self):
        res_sqrt = evaluate_expression("sqrt(144)")
        self.assertIsNotNone(res_sqrt)
        self.assertEqual(res_sqrt.result_str, "12")

        res_sin = evaluate_expression("sin(0)")
        self.assertIsNotNone(res_sin)
        self.assertEqual(res_sin.result_str, "0")

        res_sin_deg = evaluate_expression("sin(90 deg)")
        self.assertIsNotNone(res_sin_deg)
        self.assertAlmostEqual(res_sin_deg.numeric_value, 1.0)

        res_hypot = evaluate_expression("hypot(3, 4)")
        self.assertIsNotNone(res_hypot)
        self.assertEqual(res_hypot.result_str, "5")

        res_gcd = evaluate_expression("gcd(54, 24)")
        self.assertIsNotNone(res_gcd)
        self.assertEqual(res_gcd.result_str, "6")

        res_abs = evaluate_expression("abs(-42)")
        self.assertIsNotNone(res_abs)
        self.assertEqual(res_abs.result_str, "42")

        res_log = evaluate_expression("log10(1000)")
        self.assertIsNotNone(res_log)
        self.assertEqual(res_log.result_str, "3")

    def test_percentage_expressions(self):
        # 15% of 400 = 60
        res1 = evaluate_expression("15% of 400")
        self.assertIsNotNone(res1)
        self.assertEqual(res1.result_str, "60")

        # 400 + 15% = 460
        res2 = evaluate_expression("400 + 15%")
        self.assertIsNotNone(res2)
        self.assertEqual(res2.result_str, "460")

        # 400 - 15% = 340
        res3 = evaluate_expression("400 - 15%")
        self.assertIsNotNone(res3)
        self.assertEqual(res3.result_str, "340")

        # 50% = 0.5
        res4 = evaluate_expression("50%")
        self.assertIsNotNone(res4)
        self.assertEqual(res4.result_str, "0.5")

    def test_constants(self):
        res_pi = evaluate_expression("pi")
        self.assertIsNotNone(res_pi)
        self.assertTrue(res_pi.result_str.startswith("3.1415"))

    def test_safety_and_invalid_inputs(self):
        # Plain text should not trigger calculator
        self.assertIsNone(evaluate_expression("firefox"))
        self.assertIsNone(evaluate_expression("open google"))
        self.assertIsNone(evaluate_expression(""))

        # Division by zero should not raise exception
        self.assertIsNone(evaluate_expression("10 / 0"))

        # Dangerous code execution should be blocked
        self.assertIsNone(evaluate_expression("__import__('os').system('ls')"))
        self.assertIsNone(evaluate_expression("eval('1+1')"))


if __name__ == "__main__":
    unittest.main()
