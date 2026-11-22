import unittest

from part_units import convert


class PartUnitsTest(unittest.TestCase):
    def test_convert(self):
        refs_units = {"ABIA": [["btu:a.1.1"], ["btu:a.1.2", "btu:a.1.3"], ["btu:b.2.1"]]}
        reviews = [{"key": "ABIA", "assign": {"x": [0, 1], "y": [2, 0]}, "none": []}]
        out, problems = convert(reviews, refs_units)
        self.assertEqual(out["ABIA"], {"x": ["btu:a.1.1", "btu:a.1.2", "btu:a.1.3"], "y": ["btu:b.2.1", "btu:a.1.1"]})
        self.assertEqual(problems, [])

    def test_bad_index_reported(self):
        out, problems = convert([{"key": "ABIA", "assign": {"x": [7]}, "none": []}], {"ABIA": [["u"]]})
        self.assertTrue(problems)


if __name__ == "__main__":
    unittest.main()
