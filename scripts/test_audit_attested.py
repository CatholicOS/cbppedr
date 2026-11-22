import unittest

from audit_attested import audit, named, norm, stems
from export_texts import by_unit


class AuditTest(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(norm("Iohánnes Mardochæus"), "ioanes mardocaeus")
        self.assertEqual(norm("Jephthah"), "iefta")

    def test_stems_skip_common_words(self):
        e = {"names": {"la": "Mons Hor", "it": "Monte Cor", "en": "Mount Hor"}}
        self.assertEqual(stems(e), {"or", "cor"})

    def test_short_names_match_whole(self):
        keys = stems({"names": {"la": "Hor"}})
        self.assertTrue(named(norm("in monte Hor"), keys))
        self.assertFalse(named(norm("in hora illa"), keys))

    def test_inflection(self):
        keys = stems({"names": {"la": "Abner"}})
        self.assertTrue(named(norm("dixit Abneri filio Ner"), keys))

    def test_audit_flags_unnamed(self):
        entries = {"bpers:felix": {"type": "person", "names": {"la": "Felix", "en": "Felix"},
                                   "attested": ["btu:act.23.24", "btu:act.21.27"]},
                   "bevent:x": {"type": "event", "names": {"en": "Exile"}, "attested": ["btu:act.21.27"]}}
        texts = [{"btu:act.23.24": "ad Felicem praesidem", "btu:act.21.27": "Iudaei ab Asia"},
                 {"btu:act.21.27": "the Jews from Asia"}]
        self.assertEqual([(i, u) for i, u, _ in audit(entries, texts)], [("bpers:felix", "btu:act.21.27")])


class ExportTest(unittest.TestCase):
    def test_sub_verses_and_origins(self):
        refs = {(19, "1:1a@GREEK"): ["btu:est.1.1a"], (19, "1:1@HEBREW"): ["btu:est.1.1"],
                (13, "4:18a"): ["btu:1par.4.18"], (13, "4:18b"): ["btu:1par.4.18"]}
        rows = [["19", "1", "1a", "GREEK", "Anno <i>secundo</i>"], ["19", "1", "1", "HEBREW", "In diebus"],
                ["13", "4", "18a", "", "uxor"], ["13", "4", "18b", "", "Iudaia"], ["13", "9", "9", "", "x"]]
        texts, unmapped = by_unit(rows, refs)
        self.assertEqual(texts["btu:1par.4.18"], "uxor Iudaia")
        self.assertEqual(texts["btu:est.1.1a"], "Anno  secundo ")
        self.assertEqual(unmapped, 1)


if __name__ == "__main__":
    unittest.main()
