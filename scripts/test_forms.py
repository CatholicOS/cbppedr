import unittest

from forms import build, propose


def catalog(**entries):
    return {"persons": {"entries": entries}, "places": {"entries": {}}}


class ProposeTest(unittest.TestCase):
    def test_second_declension_us(self):
        self.assertEqual(propose("Petrus"), ["Petrus", "Petri", "Petro", "Petrum", "Petre"])

    def test_first_declension_a(self):
        self.assertEqual(propose("Maria"), ["Maria", "Mariae", "Mariam"])

    def test_as_names(self):
        self.assertEqual(propose("Andreas"), ["Andreas", "Andreae", "Andream"])

    def test_es_names(self):
        self.assertEqual(propose("Moyses"), ["Moyses", "Moysi", "Moysen", "Moyse"])

    def test_indeclinable_hebrew(self):
        self.assertEqual(propose("Abraham"), ["Abraham"])
        self.assertEqual(propose("Iacob"), ["Iacob"])
        self.assertEqual(propose("Bethel"), ["Bethel"])

    def test_is_has_no_rule(self):
        self.assertEqual(propose("Ioannis"), ["Ioannis"])

    def test_empty(self):
        self.assertEqual(propose(""), [])

    def test_multiword_declines_head_only(self):
        forms = propose("Ioannes Baptista")
        self.assertEqual(forms[0], "Ioannes Baptista")
        self.assertEqual(forms[1:], ["Ioanni Baptista", "Ioannen Baptista", "Ioanne Baptista"])


class BuildTest(unittest.TestCase):
    def test_sorted_by_id(self):
        out = build(catalog(**{"bpers:b": {"names": {"la": "Petrus"}}, "bpers:a": {"names": {"la": "Maria"}}}), {})
        self.assertEqual(list(out), ["bpers:a", "bpers:b"])
        self.assertEqual(out["bpers:a"], ["Maria", "Mariae", "Mariam"])

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

    def test_designation_label_verbatim(self):
        cat = catalog(**{"bpers:x": {"names": {"la": "Aaron"}, "labels": {
            "btu:1par.24.2": {"as": "designation", "editions": {"NVBSE": "patrem suum"}}}}})
        self.assertEqual(build(cat, {})["bpers:x"], ["Aaron", "patrem suum"])

    def test_label_without_nvbse_ignored_and_dedup(self):
        cat = catalog(**{"bpers:x": {"names": {"la": "Aaron"}, "labels": {
            "btu:a.1.1": {"as": "name", "editions": {"DRB": "Aaron"}},
            "btu:a.1.2": {"as": "name", "editions": {"NVBSE": "Aaron"}}}}})
        self.assertEqual(build(cat, {})["bpers:x"], ["Aaron"])

    def test_places_included(self):
        cat = {"persons": {"entries": {}}, "places": {"entries": {"bplace:r": {"names": {"la": "Roma"}}}}}
        self.assertEqual(build(cat, {})["bplace:r"], ["Roma", "Romae", "Romam"])


if __name__ == "__main__":
    unittest.main()
