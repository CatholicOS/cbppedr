import hashlib
import unittest

from export_texts import plain_by_unit


def row(book, ch, v, origin, text, tradition=""):
    return [str(book), str(ch), str(v), origin, text, tradition]


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
        rows = [row(17, 1, 1, "GREEK", "alpha", "GREEK"), row(17, 1, 1, "HEBREW", "beta", "HEBREW")]
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


if __name__ == "__main__":
    unittest.main()
