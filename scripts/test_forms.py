import unittest

from forms import build, propose


def catalog(**entries):
    return {"persons": {"entries": entries}, "places": {"entries": {}}}


class ProposeTest(unittest.TestCase):
    def test_second_declension_us(self):
        self.assertEqual(propose("Petrus"), ["Petrus", "Petri", "Petro", "Petrum", "Petre"])

    def test_first_declension_a(self):
        self.assertEqual(propose("Maria"), ["Maria", "Mariae", "Mariæ", "Mariam"])

    def test_as_names(self):
        self.assertEqual(propose("Andreas"), ["Andreas", "Andreae", "Andreæ", "Andream", "Andrea"])

    def test_es_names(self):
        self.assertEqual(propose("Moyses"), ["Moyses", "Moysis", "Moysi", "Moysem", "Moyse", "Moysen"])

    def test_ioannes_third_declension(self):
        self.assertEqual(propose("Ioannes"), ["Ioannes", "Ioannis", "Ioanni", "Ioannem", "Ioanne", "Ioannen"])

    def test_iesus_irregular(self):
        self.assertEqual(propose("Iesus"), ["Iesus", "Iesu", "Iesum"])

    def test_as_has_ablative(self):
        self.assertEqual(propose("Elias"), ["Elias", "Eliae", "Eliæ", "Eliam", "Elia"])

    def test_multiword_case_aligned(self):
        self.assertEqual(propose("Iesus Christus")[:5],
                         ["Iesus Christus", "Iesu Christi", "Iesu Christo", "Iesum Christum", "Iesu Christe"])

    def test_multiword_adds_head_forms(self):
        self.assertEqual(propose("Iesus Christus"),
                         ["Iesus Christus", "Iesu Christi", "Iesu Christo", "Iesum Christum", "Iesu Christe",
                          "Iesus", "Iesu", "Iesum"])

    def test_stoplisted_head_not_added(self):
        forms = propose("Mare Rubrum")
        self.assertNotIn("Mare", forms)
        self.assertEqual(forms[0], "Mare Rubrum")

    def test_person_multiword_adds_last_word_forms(self):
        forms = propose("Pontius Pilatus", person=True)
        self.assertEqual(forms[-5:], ["Pilatus", "Pilati", "Pilato", "Pilatum", "Pilate"])
        self.assertIn("Pontius", forms)
        self.assertLess(forms.index("Pontius"), forms.index("Pilatus"))

    def test_place_multiword_no_last_word(self):
        self.assertNotIn("Pilatus", propose("Pontius Pilatus"))

    def test_last_word_that_is_a_place_name_not_added(self):
        forms = propose("Pontius Pilatus", person=True, places=frozenset({"Pilatus"}))
        self.assertNotIn("Pilatus", forms)
        self.assertNotIn("Pilati", forms)

    def test_short_stem_keeps_only_nominative(self):
        for name in ("Mes", "Chus", "Alus", "Ara", "Sua", "Ada"):
            self.assertEqual(propose(name), [name])

    def test_stoplist_form_dropped(self):
        forms = propose("Dominus")
        self.assertEqual(forms[0], "Dominus")
        self.assertNotIn("Domine", forms)
        self.assertIn("Domini", forms)

    def test_both_ligature_spellings(self):
        self.assertEqual(propose("Azaria")[:3], ["Azaria", "Azariae", "Azariæ"])
        self.assertEqual(propose("Isræl"), ["Isræl", "Israel"])

    def test_indeclinable_hebrew(self):
        self.assertEqual(propose("Abraham"), ["Abraham"])
        self.assertEqual(propose("Iacob"), ["Iacob"])
        self.assertEqual(propose("Bethel"), ["Bethel"])

    def test_is_has_no_rule(self):
        self.assertEqual(propose("Ioannis"), ["Ioannis"])

    def test_empty(self):
        self.assertEqual(propose(""), [])

    def test_multiword_declines_each_word(self):
        forms = propose("Ioannes Baptista")
        self.assertEqual(forms[0], "Ioannes Baptista")
        self.assertEqual(forms[1:3], ["Ioannis Baptistae", "Ioannis Baptistæ"])
        self.assertIn("Ioannem Baptistam", forms)


class BuildTest(unittest.TestCase):
    def test_sorted_by_id(self):
        out = build(catalog(**{"bpers:b": {"names": {"la": "Petrus"}}, "bpers:a": {"names": {"la": "Maria"}}}), {})
        self.assertEqual(list(out), ["bpers:a", "bpers:b"])
        self.assertEqual(out["bpers:a"], ["Maria", "Mariae", "Mariæ", "Mariam"])

    def test_empty_name_without_labels_has_no_entry(self):
        self.assertEqual(build(catalog(**{"bpers:x": {"names": {"la": ""}}}), {}), {})

    def test_null_name_has_no_entry(self):
        self.assertEqual(build(catalog(**{"bpers:x": {"names": {"la": None}}}), {}), {})

    def test_build_keeps_hand_corrected(self):
        out = build(catalog(**{"bpers:x": {"names": {"la": "Petrus"}}}), {"bpers:x": ["X"]})
        self.assertEqual(out["bpers:x"], ["X"])

    def test_build_adds_nvbse_labels_of_as_name(self):
        cat = catalog(**{"bpers:x": {"names": {"la": "Petrus"}, "labels": {
            "btu:jn.1.42": {"as": "name", "editions": {"NVBSE": "Cephas", "DRB": "Cephas"}}}}})
        forms = build(cat, {})["bpers:x"]
        self.assertIn("Cephas", forms)
        self.assertIn("Cephae", forms)
        self.assertEqual(forms[0], "Petrus")

    def test_form_equal_to_another_entrys_name_kept(self):
        cat = catalog(**{"bpers:a": {"names": {"la": "Maria"}}, "bpers:b": {"names": {"la": "Mariam"}}})
        self.assertIn("Mariam", build(cat, {})["bpers:a"])
        self.assertEqual(build(cat, {})["bpers:b"][0], "Mariam")

    def test_build_person_last_word_but_place_not(self):
        cat = {"persons": {"entries": {"bpers:p": {"names": {"la": "Pontius Pilatus"}}}},
               "places": {"entries": {"bplace:p": {"names": {"la": "Pontius Pilatus"}}}}}
        out = build(cat, {})
        self.assertIn("Pilato", out["bpers:p"])
        self.assertNotIn("Pilato", out["bplace:p"])

    def test_designation_label_not_added(self):
        cat = catalog(**{"bpers:x": {"names": {"la": "Aaron"}, "labels": {
            "btu:1par.24.2": {"as": "designation", "editions": {"NVBSE": "patrem suum"}}}}})
        self.assertEqual(build(cat, {})["bpers:x"], ["Aaron"])

    def test_label_without_nvbse_ignored_and_dedup(self):
        cat = catalog(**{"bpers:x": {"names": {"la": "Aaron"}, "labels": {
            "btu:a.1.1": {"as": "name", "editions": {"DRB": "Aaron"}},
            "btu:a.1.2": {"as": "name", "editions": {"NVBSE": "Aaron"}}}}})
        self.assertEqual(build(cat, {})["bpers:x"], ["Aaron"])

    def test_places_included(self):
        cat = {"persons": {"entries": {}}, "places": {"entries": {"bplace:r": {"names": {"la": "Roma"}}}}}
        self.assertEqual(build(cat, {})["bplace:r"], ["Roma", "Romae", "Romæ", "Romam"])


if __name__ == "__main__":
    unittest.main()
