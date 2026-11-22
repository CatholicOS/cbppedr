import unittest

from refs import parse_refs


def bc(refs):
    return [(r.book, r.chapter) for r in refs]


class RefsTest(unittest.TestCase):
    def test_books_with_spaces_and_continuation(self):
        self.assertEqual(bc(parse_refs("Gn 25,6; Nm 21,11; 1 Cr 6,63", "ndeib")), [(1, 25), (4, 21), (13, 6)])
        self.assertEqual(bc(parse_refs("Sal 50,1; 75,7; 107,3", "ndeib")), [(23, 50), (23, 75), (23, 107)])

    def test_profiles_differ_on_gn(self):
        self.assertEqual(parse_refs("Gn 2,1", "bj")[0].book, 39)
        self.assertEqual(parse_refs("Gn 2,1", "ndeib")[0].book, 1)

    def test_parts_keep_ranges(self):
        self.assertEqual(parse_refs("Lc 3,23-24.29", "ndeib")[0].parts, ("23-24", "29"))
        self.assertEqual(parse_refs("Gb 40,25-41,26", "ndeib")[0].parts, ("25-41,26",))

    def test_bare_reference_far_from_book_takes_default(self):
        text = "asserviti da Davide (2Sam 8,13-14) e il nome di Giuda (cf. 29,35)."
        self.assertEqual(bc(parse_refs(text, "bj", default_book=1)), [(10, 8), (1, 29)])

    def test_chapter_only_sets_book_and_measures_skipped(self):
        self.assertEqual(bc(parse_refs("Gdc 5,4s; Sal 29; 68,8", "bj", 1)), [(7, 5), (23, 68)])
        self.assertEqual(parse_refs("circa 1,87 litri", "bj", 2), [])

    def test_unknown_book_is_not_a_reference(self):
        self.assertEqual(parse_refs("San 4,5", "ndeib"), [])


if __name__ == "__main__":
    unittest.main()
