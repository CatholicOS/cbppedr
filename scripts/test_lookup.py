import unittest

from lookup import bj_notes, nv_verse


class LookupTest(unittest.TestCase):
    def test_nv_verse(self):
        self.assertIn("Levi", nv_verse("btu:gn.29.34"))

    def test_bj_notes_for_unit(self):
        notes = bj_notes("btu:mt.14.3")
        self.assertTrue(any("Mariamne" in n["text"] for n in notes))
        self.assertTrue(all(n["page"] for n in notes))


if __name__ == "__main__":
    unittest.main()
