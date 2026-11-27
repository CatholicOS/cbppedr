import hashlib
import unittest

from export_texts import parse_plain, plain_by_unit


def row(book, ch, v, origin, text):
    return [str(book), str(ch), str(v), origin, text]


class PlainByUnit(unittest.TestCase):
    def test_plain_keeps_the_stored_text(self):
        stored = "Lorem &amp; <i>ipsum</i>  dolor"
        out, skipped = plain_by_unit([row(1, 1, 1, "", stored)], {(1, "1:1"): ["btu:a"]})
        self.assertEqual(out["btu:a"]["text"], stored)
        self.assertEqual(skipped, 0)

    def test_hash_is_sha256_hex(self):
        out, _ = plain_by_unit([row(1, 1, 1, "", "Verbum é")], {(1, "1:1"): ["btu:a"]})
        self.assertEqual(out["btu:a"]["hash"], hashlib.sha256("Verbum é".encode("utf-8")).hexdigest())

    def test_esther_gets_both_traditions(self):
        refs = {(17, "1:1@GREEK"): ["btu:e"], (17, "1:1@HEBREW"): ["btu:e"]}
        rows = [row(17, 1, 1, "GREEK", "alpha"), row(17, 1, 1, "HEBREW", "beta")]
        out, skipped = plain_by_unit(rows, refs)
        self.assertEqual(set(out), {"btu:e@GREEK", "btu:e@HEBREW"})
        self.assertEqual(out["btu:e@HEBREW"]["text"], "beta")
        self.assertEqual(skipped, 0)

    def test_unit_over_two_rows_is_skipped(self):
        refs = {(1, "1:1"): ["btu:a", "btu:b"], (1, "1:2"): ["btu:a"]}
        out, skipped = plain_by_unit([row(1, 1, 1, "", "x"), row(1, 1, 2, "", "y")], refs)
        self.assertEqual(set(out), {"btu:b"})
        self.assertEqual(skipped, 1)

    def test_row_over_several_units_feeds_each(self):
        out, _ = plain_by_unit([row(1, 1, 1, "", "x")], {(1, "1:1"): ["btu:a", "btu:b"]})
        self.assertEqual(out["btu:a"]["text"], out["btu:b"]["text"])

    def test_origin_fallback_when_map_is_not_split(self):
        out, _ = plain_by_unit([row(1, 1, 1, "GREEK", "x")], {(1, "1:1"): ["btu:a"]})
        self.assertIn("btu:a", out)

    def test_esther_unit_over_two_rows_of_one_text_is_skipped(self):
        refs = {(17, "1:1@GREEK"): ["btu:e"], (17, "1:2@GREEK"): ["btu:e"], (17, "1:1@HEBREW"): ["btu:e"]}
        rows = [row(17, 1, 1, "GREEK", "a"), row(17, 1, 2, "GREEK", "b"), row(17, 1, 1, "HEBREW", "c")]
        out, skipped = plain_by_unit(rows, refs)
        self.assertEqual(out, {})
        self.assertEqual(skipped, 1)

    def test_single_tradition_keeps_the_plain_key(self):
        out, _ = plain_by_unit([row(17, 1, 1, "GREEK", "a")], {(17, "1:1@GREEK"): ["btu:e"]})
        self.assertEqual(set(out), {"btu:e"})


class ParsePlain(unittest.TestCase):
    def test_tab_inside_text_does_not_shift_fields(self):
        out = "1\t2\t3\tGREEK\tone\ttwo\x1e1\t2\t4\t\tthree\nline\n"
        self.assertEqual(parse_plain(out), [["1", "2", "3", "GREEK", "one\ttwo"], ["1", "2", "4", "", "three\nline"]])

    def test_short_row_raises_naming_it(self):
        with self.assertRaisesRegex(ValueError, "row 2"):
            parse_plain("1\t2\t3\t\tx\x1e1\t2\t3\n")

    def test_empty_output(self):
        self.assertEqual(parse_plain(""), [])


if __name__ == "__main__":
    unittest.main()
