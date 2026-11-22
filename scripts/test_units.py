import unittest

from refs import parse_refs
from units import units_for


def first(text, profile="ndeib"):
    return units_for(parse_refs(text, profile)[0])


class UnitsTest(unittest.TestCase):
    def test_single_verse(self):
        self.assertEqual(first("Gn 29,34"), ["btu:gn.29.34"])

    def test_range_in_chapter(self):
        self.assertEqual(first("Lc 3,23-24"), ["btu:lc.3.23", "btu:lc.3.24"])

    def test_list_of_verses(self):
        self.assertEqual(first("Lc 3,24.29"), ["btu:lc.3.24", "btu:lc.3.29"])

    def test_cross_chapter_range(self):
        got = first("Gb 40,32-41,2")
        self.assertEqual(got[0], "btu:iob.40.32")
        self.assertIn("btu:iob.41.1", got)

    def test_other_numbering_is_unresolved(self):
        self.assertIsNone(first("Sal 151,2"))

    def test_cei_numbering_resolves(self):
        self.assertIsNotNone(first("Gb 40,25"))

    def test_greek_esther(self):
        got = first("Est 1,1a", "bj")
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0].startswith("btu:est."))


if __name__ == "__main__":
    unittest.main()
