import unittest

from audit_attested import audit, named, norm, stems
from export_texts import by_unit


class AuditTest(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(norm("Iohánnes Mardochæus"), "ioanes mardocaeus")
        self.assertEqual(norm("Jephthah"), "iefta")

    def test_stems_skip_common_words(self):
        e = {"names": {"la": "Mons Hor", "it": "Monte Cor", "en": "Mount Hor"}}
        self.assertEqual(stems(e), {"=hor", "=cor"})

    def test_short_names_match_whole(self):
        keys = stems({"names": {"la": "Hor"}})
        self.assertTrue(named("in monte Hor", keys))
        self.assertFalse(named("in hora illa", keys))

    def test_place_matches_on_its_head_word(self):
        keys = stems({"type": "place", "names": {"la": "Bethania trans Iordanem", "en": "Bethany beyond the Jordan"}})
        self.assertFalse(named("baptizatus est in Iordane", keys))
        self.assertTrue(named("in Bethania trans Iordanem", keys))

    def test_stop_words_are_normalized(self):
        self.assertEqual(stems({"names": {"en": "Alexander the Great"}}), {"alexand*", "grea*"})
        self.assertEqual(stems({"type": "place", "names": {"en": "Valley of Hinnom"}}), {"inom*"})

    def test_short_names_keep_h_and_skip_function_words(self):
        self.assertFalse(named("et dixit", stems({"names": {"la": "Heth"}})))
        self.assertTrue(named("filii Heth", stems({"names": {"la": "Heth"}})))
        self.assertEqual(stems({"names": {"la": "On", "en": "On"}}), set())

    def test_inflection(self):
        keys = stems({"names": {"la": "Abner"}})
        self.assertTrue(named("dixit Abneri filio Ner", keys))

    def test_audit_flags_unnamed(self):
        entries = {"bpers:felix": {"type": "person", "names": {"la": "Felix", "en": "Felix"},
                                   "attested": ["btu:act.23.24", "btu:act.21.27"]},
                   "bevent:x": {"type": "event", "names": {"en": "Exile"}, "attested": ["btu:act.21.27"]}}
        texts = [{"btu:act.23.24": "ad Felicem praesidem", "btu:act.21.27": "Iudaei ab Asia"},
                 {"btu:act.21.27": "the Jews from Asia"}]
        self.assertEqual([(i, u) for i, u, _ in audit(entries, texts)], [("bpers:felix", "btu:act.21.27")])


    def test_labelled_unit_accounted_for(self):
        entries = {"bpers:petrus": {"type": "person", "names": {"la": "Petrus"}, "attested": ["btu:gal.2.9"],
                                    "labels": {"btu:gal.2.9": {"as": "name", "editions": {"NVBSE": "Cephas"}}}}}
        self.assertEqual(audit(entries, [{"btu:gal.2.9": "Iacobus et Cephas"}]), [])


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

    def test_origin_fallback_only_when_the_map_does_not_split(self):
        refs = {(19, "1:1@HEBREW"): ["btu:est.1.1"], (19, "1:1"): ["btu:est.1.1"], (17, "2:3"): ["btu:tb.2.3"]}
        texts, unmapped = by_unit([["19", "1", "1", "GREEK", "x"], ["17", "2", "3", "GREEK", "Tobias &amp; Anna"]], refs)
        self.assertEqual((texts, unmapped), ({"btu:tb.2.3": "Tobias & Anna"}, 1))


if __name__ == "__main__":
    unittest.main()
