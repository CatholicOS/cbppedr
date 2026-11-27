import hashlib
import unittest

from extract_mentions import check, extract, find, resolve, utf16


def texts(**units):
    """Invented sentences by unit key (a `__` in the key stands for `@`)."""
    out = {}
    for key, text in units.items():
        key = "btu:" + key.replace("__", "@").replace("_", ".")
        out[key] = {"text": text, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    return out


def catalogs(persons=None, places=None):
    return {"persons": {"entries": persons or {}}, "places": {"entries": places or {}}}


def person(*attested, labels=None):
    entry = {"type": "person", "attested": list(attested)}
    if labels:
        entry["labels"] = labels
    return entry


def designation(text):
    return {"as": "designation", "editions": {"NVBSE": text, "VGCL": text}}


class UnitHelpersTest(unittest.TestCase):
    def test_utf16_counts_astral_as_two(self):
        self.assertEqual(utf16("a𝔄b", 2), 3)
        self.assertEqual(utf16("abc", 2), 2)

    def test_check_is_first_8_hex_of_sha256(self):
        self.assertEqual(check("Petrus"), hashlib.sha256("Petrus".encode("utf-8")).hexdigest()[:8])
        self.assertEqual(len(check("Petrus")), 8)


class FindTest(unittest.TestCase):
    def test_whole_words_only(self):
        forms = {"bpers:petrus": ["Petrus", "Petri"]}
        self.assertEqual(find("Petrusque venit", forms), [])
        self.assertEqual(find("domus Petri", forms), [(6, 11, "bpers:petrus")])
        self.assertEqual(find("xPetri", forms), [])

    def test_non_ascii_letters_are_letters(self):
        forms = {"bpers:petrus": ["Petrus"]}
        self.assertEqual(find("Petrusë", forms), [])
        self.assertEqual(find("æPetrus", forms), [])
        self.assertEqual(find("(Petrus),", forms), [(1, 7, "bpers:petrus")])

    def test_initial_capital(self):
        forms = {"bpers:petrus": ["Petrus"], "bpers:pharao": ["rex Aegypti"]}
        self.assertEqual(find("et petrus abiit", forms), [])
        self.assertEqual(find("dixit rex Aegypti", forms), [(6, 17, "bpers:pharao")])

    def test_lower_case_single_word_form_is_not_a_name(self):
        forms = {"bloc:via-maris": ["via maris", "via", "viam"]}
        self.assertEqual(find("in via et viam", forms), [])
        self.assertEqual(find("in via maris", forms), [(3, 12, "bloc:via-maris")])

    def test_longest_form_first_at_a_position(self):
        forms = {"bpers:simon": ["Simon"], "bpers:petrus": ["Simon Petrus", "Petrus"]}
        self.assertEqual(find("Simon Petrus dixit", forms),
                         [(0, 12, "bpers:petrus"), (6, 12, "bpers:petrus")])

    def test_shared_form_gives_one_hit_per_entry(self):
        forms = {"bpers:b": ["Zacharias"], "bpers:a": ["Zacharias"]}
        self.assertEqual(find("Zacharias", forms), [(0, 9, "bpers:a"), (0, 9, "bpers:b")])


class ResolveTest(unittest.TestCase):
    def test_designation_is_settled_even_if_a_stop_word(self):
        hits = [(0, 5, "bpers:x")]
        self.assertEqual(resolve("puero", hits, set(), designated={(0, 5, "bpers:x")}),
                         [{"start": 0, "end": 5, "check": check("puero"), "entry": "bpers:x"}])

    def test_unattested_unique_form_needs_outside_leave(self):
        self.assertIn("candidates", resolve("Vita", [(0, 4, "bpers:x")], set())[0])
        self.assertEqual(resolve("Vita", [(0, 4, "bpers:x")], set(), outside=lambda w, i: True)[0]["entry"], "bpers:x")

    def test_stop_word_attested_is_settled(self):
        self.assertEqual(resolve("Vita", [(0, 4, "bpers:x")], {"bpers:x"}),
                         [{"start": 0, "end": 4, "check": check("Vita"), "entry": "bpers:x"}])


class ExtractTest(unittest.TestCase):
    def run_one(self, text, forms, persons=None, places=None, stop=frozenset(), key="gn_1_1", partial=None):
        """Without catalogs, every entry of `forms` is attested elsewhere in the same book (Genesis)."""
        if persons is None and places is None:
            persons = {id_: person("btu:gn.50.1") for id_ in forms}
        body, report = extract(texts(**{key: text}), forms, catalogs(persons, places), stop, partial)
        unit = next(iter(body["units"].values()), None)
        return (unit["mentions"] if unit else []), report

    def test_unique_name_is_settled(self):
        mentions, _ = self.run_one("Et dixit Petrus ad eos", {"bpers:petrus": ["Petrus"]})
        self.assertEqual(mentions, [{"start": 9, "end": 15, "check": check("Petrus"), "entry": "bpers:petrus"}])

    def test_body_shape(self):
        body, _ = extract(texts(gn_1_1="Et dixit Petrus", gn_1_2="nihil"), {"bpers:petrus": ["Petrus"]},
                          catalogs({"bpers:petrus": person("btu:gn.50.1")}), frozenset())
        self.assertEqual(body["edition"], "NVBSE")
        self.assertIn("$comment", body)
        self.assertEqual(list(body["units"]), ["btu:gn.1.1"])
        self.assertEqual(body["units"]["btu:gn.1.1"]["hash"],
                         hashlib.sha256("Et dixit Petrus".encode("utf-8")).hexdigest())

    def test_shared_name_settled_by_attestation(self):
        forms = {"bpers:zacharias.a": ["Zacharias"], "bpers:zacharias.b": ["Zacharias"]}
        persons = {"bpers:zacharias.a": person("btu:lc.1.5"), "bpers:zacharias.b": person("btu:zac.1.1")}
        mentions, _ = self.run_one("Fuit Zacharias", forms, persons, key="lc_1_5")
        self.assertEqual(mentions[0]["entry"], "bpers:zacharias.a")
        self.assertNotIn("candidates", mentions[0])

    def test_shared_name_unattested_is_under_review(self):
        forms = {"bpers:zacharias.b": ["Zacharias"], "bpers:zacharias.a": ["Zacharias"]}
        mentions, report = self.run_one("Fuit Zacharias", forms)
        self.assertEqual(mentions, [{"start": 5, "end": 14, "check": check("Zacharias"),
                                     "candidates": ["bpers:zacharias.a", "bpers:zacharias.b"]}])
        self.assertEqual(report["under_review"][0]["words"], "Zacharias")

    def test_shared_name_attested_by_both_is_under_review(self):
        forms = {"bpers:z.a": ["Zacharias"], "bpers:z.b": ["Zacharias"]}
        persons = {"bpers:z.a": person("btu:gn.1.1"), "bpers:z.b": person("btu:gn.1.1")}
        mentions, _ = self.run_one("Fuit Zacharias", forms, persons)
        self.assertEqual(mentions[0]["candidates"], ["bpers:z.a", "bpers:z.b"])

    def test_person_and_place_sharing_a_form_is_shared(self):
        forms = {"bpers:edom": ["Edom"], "bloc:edom": ["Edom"]}
        mentions, _ = self.run_one("in Edom", forms)
        self.assertEqual(mentions[0]["candidates"], ["bloc:edom", "bpers:edom"])

    def test_stop_word_form_is_a_candidate_of_one(self):
        mentions, _ = self.run_one("Vita longa est", {"bpers:vita": ["Vita"]}, stop=frozenset({"vita"}))
        self.assertEqual(mentions, [{"start": 0, "end": 4, "check": check("Vita"), "candidates": ["bpers:vita"]}])

    def test_every_occurrence_is_marked(self):
        mentions, _ = self.run_one("Petrus et Petrus", {"bpers:petrus": ["Petrus"]})
        self.assertEqual([(m["start"], m["end"]) for m in mentions], [(0, 6), (10, 16)])

    def test_nested_spans_kept_crossing_dropped(self):
        forms = {"bpers:pharao": ["rex Aegypti"], "bloc:aegyptus": ["Aegypti"]}
        mentions, report = self.run_one("dixit rex Aegypti", forms)
        self.assertEqual([(m["start"], m["end"], m["entry"]) for m in mentions],
                         [(6, 17, "bpers:pharao"), (10, 17, "bloc:aegyptus")])
        self.assertEqual(report["crossing"], [])
        forms = {"bpers:a": ["Alpha Beta"], "bpers:b": ["Beta Gamma"], "bpers:c": ["Delta"]}
        mentions, report = self.run_one("Alpha Beta Gamma Delta", forms)
        self.assertEqual([m["entry"] for m in mentions], ["bpers:c"])
        self.assertEqual(len(report["crossing"]), 1)
        crossing = report["crossing"][0]
        self.assertEqual(crossing["unit"], "btu:gn.1.1")
        self.assertEqual(sorted(s["words"] for s in crossing["spans"]), ["Alpha Beta", "Beta Gamma"])
        self.assertEqual(report["counts"]["crossing"], 2)

    def test_positions_are_utf16(self):
        mentions, _ = self.run_one("𝔄 Petrus", {"bpers:petrus": ["Petrus"]})
        self.assertEqual((mentions[0]["start"], mentions[0]["end"]), (3, 9))

    def test_attested_entry_not_found_is_reported(self):
        persons = {"bpers:petrus": person("btu:gn.1.1"), "bpers:paulus": person("btu:gn.1.1")}
        _, report = self.run_one("Petrus venit", {"bpers:petrus": ["Petrus"], "bpers:paulus": ["Paulus"]},
                                 persons)
        self.assertEqual(report["unmatched"], [{"unit": "btu:gn.1.1", "entry": "bpers:paulus"}])
        self.assertEqual(report["counts"]["unmatched"], 1)

    def test_designation_settled_only_in_its_unit(self):
        persons = {"bpers:aaron": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("patrem suum")})}
        body, report = extract(texts(gn_1_1="vidit patrem suum", gn_1_2="vidit patrem suum"),
                               {"bpers:aaron": ["Aaron"]}, catalogs(persons), frozenset({"patrem"}))
        self.assertEqual(list(body["units"]), ["btu:gn.1.1"])
        self.assertEqual(body["units"]["btu:gn.1.1"]["mentions"],
                         [{"start": 6, "end": 17, "check": check("patrem suum"), "entry": "bpers:aaron"}])
        self.assertEqual(report["unmatched"], [])

    def test_lower_case_single_word_designation_is_looked_for(self):
        persons = {"bpers:x": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("puero")})}
        mentions, _ = self.run_one("dixit puero", {"bpers:x": ["Xystus"]}, persons)
        self.assertEqual(mentions, [{"start": 6, "end": 11, "check": check("puero"), "entry": "bpers:x"}])

    def test_name_label_is_not_read_from_the_catalog(self):
        persons = {"bpers:petrus": person("btu:gn.1.1", labels={
            "btu:gn.1.1": {"as": "name", "editions": {"NVBSE": "Cephas"}}})}
        mentions, report = self.run_one("Cephas venit", {"bpers:petrus": ["Petrus"]}, persons)
        self.assertEqual(mentions, [])
        self.assertEqual(report["unmatched"], [{"unit": "btu:gn.1.1", "entry": "bpers:petrus"}])

    def test_esther_suffix_dropped_for_attestation_and_designation(self):
        forms = {"bpers:mardochaeus.a": ["Mardochaeus"], "bpers:mardochaeus.b": ["Mardochaeus"]}
        persons = {"bpers:mardochaeus.a": person("btu:est.2.5"), "bpers:mardochaeus.b": person("btu:esd.2.2"),
                   "bpers:assuerus": person("btu:est.2.5", labels={"btu:est.2.5": designation("regis")})}
        body, report = extract(texts(est_2_5__HEBREW="Mardochaeus servus regis", est_2_5__GREEK="Mardochaeus"),
                               forms | {"bpers:assuerus": ["Assuerus"]}, catalogs(persons), frozenset())
        hebrew = body["units"]["btu:est.2.5@HEBREW"]["mentions"]
        self.assertEqual([m["entry"] for m in hebrew], ["bpers:mardochaeus.a", "bpers:assuerus"])
        self.assertEqual(body["units"]["btu:est.2.5@GREEK"]["mentions"][0]["entry"], "bpers:mardochaeus.a")
        # found in one of Esther's two texts: the attestation is matched
        self.assertEqual(report["unmatched"], [])

    def test_unique_name_attested_only_in_another_book_is_under_review(self):
        # a Susanna-like case: the catalog's only bearer of the name is attested in another book
        persons = {"bpers:susanna": person("btu:lc.8.3")}
        mentions, _ = self.run_one("Erat Susanna pulchra", {"bpers:susanna": ["Susanna"]}, persons, key="dn_13_2")
        self.assertEqual(mentions, [{"start": 5, "end": 12, "check": check("Susanna"),
                                     "candidates": ["bpers:susanna"]}])

    def test_unique_name_attested_in_the_same_book_is_settled(self):
        persons = {"bpers:susanna": person("btu:dn.13.1")}
        mentions, _ = self.run_one("Erat Susanna pulchra", {"bpers:susanna": ["Susanna"]}, persons, key="dn_13_2")
        self.assertEqual(mentions[0]["entry"], "bpers:susanna")

    def test_mentioned_does_not_count_for_the_book(self):
        persons = {"bpers:susanna": dict(person("btu:lc.8.3"), mentioned=["btu:dn.13.1"])}
        mentions, _ = self.run_one("Erat Susanna", {"bpers:susanna": ["Susanna"]}, persons, key="dn_13_2")
        self.assertEqual(mentions[0]["candidates"], ["bpers:susanna"])

    def test_partial_form_outside_attested_units_is_under_review(self):
        forms = {"bplace:tres-tabernae": ["Tres Tabernae", "Tres"]}
        places = {"bplace:tres-tabernae": person("btu:act.28.15")}
        mentions, _ = self.run_one("Tres viri", forms, places=places, key="act_28_1",
                                   partial={"bplace:tres-tabernae": ["Tres"]})
        self.assertEqual(mentions[0]["candidates"], ["bplace:tres-tabernae"])
        mentions, _ = self.run_one("ad Tres Tabernae et Tres", forms, places=places, key="act_28_15",
                                   partial={"bplace:tres-tabernae": ["Tres"]})
        self.assertEqual([m["entry"] for m in mentions], ["bplace:tres-tabernae"] * 2)

    def test_partial_form_inside_an_attested_unit_is_settled(self):
        forms = {"bpers:simon-petrus": ["Simon Petrus", "Petrus"]}
        persons = {"bpers:simon-petrus": person("btu:gn.1.1")}
        mentions, _ = self.run_one("dixit Petrus", forms, persons, partial={"bpers:simon-petrus": ["Petrus"]})
        self.assertEqual(mentions[0]["entry"], "bpers:simon-petrus")

    def test_stop_form_outside_attested_units_is_under_review_inside_settled(self):
        persons = {"bplace:media": person("btu:gn.1.1")}
        mentions, _ = self.run_one("Media nocte", {"bplace:media": ["Media"]}, places=persons,
                                   stop=frozenset({"media"}), key="gn_1_2")
        self.assertEqual(mentions[0]["candidates"], ["bplace:media"])
        mentions, _ = self.run_one("in Media", {"bplace:media": ["Media"]}, places=persons,
                                   stop=frozenset({"media"}))
        self.assertEqual(mentions[0]["entry"], "bplace:media")

    def test_esther_book_is_est(self):
        persons = {"bpers:aman": person("btu:est.3.1")}
        body, _ = extract(texts(est_3_2__GREEK="Aman"), {"bpers:aman": ["Aman"]}, catalogs(persons), frozenset())
        self.assertEqual(body["units"]["btu:est.3.2@GREEK"]["mentions"][0]["entry"], "bpers:aman")

    def test_counts(self):
        forms = {"bpers:petrus": ["Petrus"], "bpers:z.a": ["Zacharias"], "bpers:z.b": ["Zacharias"]}
        _, report = self.run_one("Petrus et Zacharias", forms)
        self.assertEqual(report["counts"]["settled"], 1)
        self.assertEqual(report["counts"]["under_review"], 1)
        self.assertEqual(report["counts"]["units"], 1)


if __name__ == "__main__":
    unittest.main()
