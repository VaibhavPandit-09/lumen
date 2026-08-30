"""
Unit tests for deterministic physical and data size unit conversions.
"""

import unittest
from lumen.core.units import parse_and_convert_unit


class TestUnits(unittest.TestCase):

    def test_length_conversions(self):
        # 1 km in meters
        res = parse_and_convert_unit("1 km in m")
        self.assertIsNotNone(res)
        self.assertAlmostEqual(res.to_val, 1000.0)

        # 100 km in miles
        res2 = parse_and_convert_unit("100 km to miles")
        self.assertIsNotNone(res2)
        self.assertAlmostEqual(res2.to_val, 62.1371, places=3)

    def test_temperature_conversions(self):
        # 32 F in C
        res = parse_and_convert_unit("32 F in C")
        self.assertIsNotNone(res)
        self.assertAlmostEqual(res.to_val, 0.0)

        # 100 C in F
        res2 = parse_and_convert_unit("100 C to F")
        self.assertIsNotNone(res2)
        self.assertAlmostEqual(res2.to_val, 212.0)

        # 0 C in K
        res3 = parse_and_convert_unit("0 C in K")
        self.assertIsNotNone(res3)
        self.assertAlmostEqual(res3.to_val, 273.15)

    def test_speed_conversions(self):
        res = parse_and_convert_unit("100 km/h in mph")
        self.assertIsNotNone(res)
        self.assertAlmostEqual(res.to_val, 62.1371, places=3)

    def test_data_size_conversions(self):
        res = parse_and_convert_unit("2 GB in MB")
        self.assertIsNotNone(res)
        self.assertAlmostEqual(res.to_val, 2000.0)

        res_bin = parse_and_convert_unit("1024 KiB in MiB")
        self.assertIsNotNone(res_bin)
        self.assertAlmostEqual(res_bin.to_val, 1.0)

    def test_mass_conversions(self):
        res = parse_and_convert_unit("5 kg in lbs")
        self.assertIsNotNone(res)
        self.assertAlmostEqual(res.to_val, 11.0231, places=3)

    def test_invalid_query_returns_none(self):
        self.assertIsNone(parse_and_convert_unit("hello world"))
        self.assertIsNone(parse_and_convert_unit("5 kg in invalid_unit_xyz"))


if __name__ == "__main__":
    unittest.main()
